from app import settings
import logging
from app.twitch_client import TwitchStreamer
from py2neo import Graph, Node
from py2neo.ogm import GraphObject, Property, Label, RelatedTo, RelatedFrom

module_logger = logging.getLogger(__name__+'.py')

# for logging in fxn def outside class def
# https://docs.python.org/3/howto/logging-cookbook.html#using-logging-in-multiple-modules
# module_logger = logging.getLogger('spam_application.auxiliary')
# TODO: END OF DAY GOAL -- ADD FOLLOWERS TO STREAMER; ADD FOLLOWERS AS 'USERS' IN DB
# inspect.currentframe().f_code.co_name    gets name of outer function (for logging?)

# DEFINITIONS FOR GRAPH DB OBJECTS
class UserGraphObj(GraphObject):
    # The primary node label used for Cypher MATCH and MERGE operations
    __primarylabel__ = 'User'
    # The primary property key used for Cypher MATCH and MERGE operations
    __primarykey__ = 'twitch_uid'

    # PROPERTIES
    twitch_uid = Property('twitch_uid')
    name = Property('name')
    display_name = Property('display_name')
    broadcaster_type = Property('broadcaster_type')

    # RELATIONSHIPS
    is_following = RelatedTo('Streamer', 'IS_FOLLOWING')
    is_followed_by = RelatedFrom('User', 'IS_FOLLOWED_BY')

    def __init__(self, twitch_uid):
        self.twitch_uid = twitch_uid


class StreamerNode(UserGraphObj):
    __primarylabel__ = 'Streamer'
    # PROPERTIES
    profile_img_url = Property()
    # LABELS
    #   A Label defined on a GraphObject provides an accessor to a label of the underlying central node.
    #   It is exposed as a boolean value, the setting of which allows the label to be toggled on or off.
    streamer = Label('Streamer')

    is_followed_by = RelatedFrom('User', 'IS_FOLLOWED_BY')
    is_following = RelatedTo('Streamer', 'IS_FOLLOWING')



class Neo4jDB:
    def __init__(self, host_addr: str = 'localhost'):
        # Initialize logger
        self.logger = logging.getLogger(__name__+'.py')
        self.logger.info('Creating an instance of "Neo4jDB"')
        # Establish a connection to neo4j db
        self.logger.info('Connecting to neo4j DB ...')
        self.db = Graph(auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD), host=host_addr)
        self.logger.info('... Connected to neo4j DB named: "{}"'.format(self.db.name))

    def create_streamer_node(self, some_streamer) -> StreamerNode:
        streamer_node = StreamerNode(some_streamer.twitch_uid)
        streamer_node.display_name = some_streamer.display_name
        streamer_node.name = some_streamer.name
        streamer_node.profile_img_url = some_streamer.prof_img_url
        streamer_node.streamer = True
        # Push Changes to DB for New Streamer
        module_logger.info("Merging {} to DB".format(some_streamer.display_name))
        self.db.merge(streamer_node)

        return streamer_node

    def add_streamer_folls_from_twitch(self, some_streamer: TwitchStreamer, streamer_node: StreamerNode):
        followers_dict = some_streamer.get_all_follows()
        module_logger.info('Adding Followers to DB for {} ...'.format(some_streamer.display_name))
        # Add followers in followers list as nodes
        for each_hundred_list in followers_dict.values():
            for each_follower_dict in each_hundred_list:
                follower_uid = each_follower_dict['from_id']
                some_follower = UserGraphObj(follower_uid)
                some_follower.followed_at = each_follower_dict['followed_at']
                some_follower.display_name = each_follower_dict['from_name']
                # Add Follower/Following Relationship between Streamer and Follower
                #TODO: BREAKS HERE: "module 'neo4db' has no attribute 'Streamer'"
                some_follower.is_following(streamer_node)
                # Create or Update Follower in DB
                self.db.merge(some_follower)
                module_logger('DB: Added {} as a follower of {}'.format(some_follower.display_name, some_streamer.display_name))
                # Update Streamer Node Relationship in DB
                self.db.push(streamer_node.is_followed_by(some_follower))
                module_logger('Added "is following" relationship for {}'.format(some_follower.display_name))

    def find_or_add_streamer(self, streamer_name: str):
        # Lookup streamer_name using twitch_client to fetch twitch_uid
        try:
            streamer = TwitchStreamer(str(streamer_name))
            twitch_api_succ_msg = "find_or_add_streamer() => Twitch API - 'validate_name()' found user: "
            twitch_api_succ_msg += '"{}"'.format(streamer.display_name)
            twitch_api_succ_msg += ' (uid: {})'.format(streamer.twitch_uid)
            self.logger.info(twitch_api_succ_msg)
        except ValueError:
            twitch_api_fail_msg = "'find_or_add_streamer()' => Twitch API user NOT found: "
            twitch_api_fail_msg += '"{}"'.format(str(streamer_name))
            self.logger.info(twitch_api_fail_msg)
            return None

        # Search DB for node matching
        user_node = Node('User', 'Streamer',
                         twitch_uid=str(streamer.twitch_uid),
                         name=str(streamer.name),
                         display_name=str(streamer.display_name),
                         total_followers=str(streamer.total_followers),
                         profile_img_url=str(streamer.prof_img_url))

        streamer_node = StreamerNode()
        streamer_node.twitch_uid = streamer.twitch_uid
        streamer_node.display_name = streamer.display_name
        streamer_node.name = streamer.name
        streamer_node.profile_img_url = streamer.prof_img_url


        #self.db.create(user_node)
        print(self.db.nodes)

        # # Check DB for unique twitch uid
        # uid_node = Node('User', twitch_id=str(streamer.uid))
        # self.logger.info('Checking Neo4j DB for matching twitch uid')
        # #matcher = NodeMatcher(self.db)
        # matcher = NodeMatcher(self.db).match(uid_node)
        # print('matcher', matcher)
        #
        # # TODO: Use MERGE to create if not exists
        # # If DB match not found, try less-restrictive
        # if matcher is None:
        #     self.logger.info('No Match found, attempting to add user to DB.')
        #     new_user_node = Node('User',
        #                          twitch_id=streamer.uid,
        #                          name=streamer.name,
        #                          display_name=streamer.display_name,
        #                          total_followers=streamer.total_followers,
        #                          profile_img_url=streamer.prof_img_url)
        #     self.db.create(new_user_node)
        #     self.logger.info('New user was created in DB')
        #
        #     # Add uid, profile img url, name, total_twitch_followers (as reported by Twitch)
        #
        #     # Add follower list relationships from streamer.get_follows
        #
        # # Node found in DB
        # else:
        #     twitch_total_followers = streamer.total_followers
        #     # Check if node_total_followers field exists in found node
        #
        #     # Check if node_total_followers field  is current (equal to twitch_total_followers)
        #         # Update follower relationships if 'node_total_followers' != twitch_total_followers
        #
        #     # Check COUNT of follower relationships in DB
        #
        #         # Update follower relationships if COUNT does not match 'node_total_followers'
        #
        #         # Update follower relationships if COUNT does not match 'total_twitch_followers'


        pass


