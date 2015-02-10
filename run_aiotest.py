import aiotest.run
import aiouv

config = aiotest.TestConfig()
config.new_event_pool_policy = aiouv.EventLoopPolicy
aiotest.run.main(config)
