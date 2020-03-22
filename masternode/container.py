""" Main dependency injection container for Veles Masternode,
    simple declarative container until the projects gets bigger """

import logging
from dependency_injector import containers, providers

from . import appcontext
from . import appconfig
from . import mnsync_service
from . import signing_service
from . import remote_gateway
from .blockchain import core_node_service
from .jobs import discovery_daemon, metric_daemon, web_server
from .controllers import masternode_status, masternode_list
from .dapps import registry


class IocContainer(containers.DeclarativeContainer):
    """Application IoC container."""
    db_type = 'mem'
    config = providers.Configuration('config')
    logger = providers.Singleton(logging.Logger, name='VelesMasternode')


    # Core app components
    app_config = providers.Singleton(
        appconfig.ApplicationConfig,
        filename=config.config
    )

    # Gateways, repos
    if db_type == 'redis':
        from .persistence.repository import redis

        redis_gateway = providers.Singleton(
            redis.RedisGateway,
            config=app_config
        )
        repos = {
            'MasternodeRepository': providers.Singleton(
                redis.MasternodeRepository,
                redis_gateway=redis_gateway
            ),
            'MetricRepository': providers.Singleton(
                redis.MetricRepository,
                redis_gateway=redis_gateway
            )
        }
    else:
        from .persistence.repository import mem

        repos = {
            'MasternodeRepository': providers.Singleton(
                mem.MasternodeRepository
            ),
            'MetricRepository': providers.Singleton(
                mem.MetricRepository
            )
        } 
    masternode_gateway = providers.Singleton(
        remote_gateway.RemoteMasternodeGateway,
        config=app_config,
        logger=logger
    )

    # Services
    services = {
        'CoreNodeService': providers.Singleton(
            core_node_service.CoreNodeService,
            config=app_config,
            logger=logger
        )
    }
    services.update({
        'MasternodeSyncService': providers.Singleton(
            mnsync_service.MasternodeSyncService,
            masternode_repo=repos['MasternodeRepository'],
            core_node_service=services['CoreNodeService'],
            logger=logger
        )
    })
    services.update({
        'MasternodeSigningService': providers.Singleton(
            signing_service.MasternodeSigningService,
            core_node_service=services['CoreNodeService'],
            mnsync_service=services['MasternodeSyncService'],
            config=app_config,
            logger=logger
        )
    })

    # Repos/Services accessible for other provider classes
    metric_repository = repos['MetricRepository']
    mn_signing_service = services['MasternodeSigningService']
    mn_sync_service = services['MasternodeSyncService']

    # Dapps
    dapp_registry = providers.Factory(
        registry.dAppRegistry,
        config=app_config,
        logger=logger,
    )

    # Controllers
    controllers = {
        'MasternodeStatusController': providers.Factory(
            masternode_status.MasternodeStatusController,
            config=app_config,
            logger=logger,
            signing_service=services['MasternodeSigningService'],
            core_node=services['CoreNodeService'],
            dapp_registry=dapp_registry
        ),
        'MasternodeListController': providers.Factory(
            masternode_list.MasternodeListController,
            config=app_config,
            logger=logger,
            signing_service=services['MasternodeSigningService'],
            mnsync_service=services['MasternodeSyncService']
        )
    }

    # Jobs
    jobs = {
        'DiscoveryDaemon': providers.Factory(
            discovery_daemon.DiscoveryDaemon,
            mnsync_service=services['MasternodeSyncService'],
            masternode_gateway=masternode_gateway,
            config=app_config,
            logger=logger
        ),
        'MetricDaemon': providers.Factory(
            metric_daemon.MetricDaemon,
            metric_repository=repos['MetricRepository'],
            dapp_registry=dapp_registry,
            config=app_config,
            logger=logger
        ),
        'WebServer': providers.Factory(
            web_server.WebServer,
            controllers=controllers,
            dapp_registry=dapp_registry,
            config=app_config,
            logger=logger
        ),
    }

    # Main app entry point
    app = providers.Singleton(
        appcontext.ApplicationContext,
        logger=logger,
        jobs=jobs
        )

    get_controllers = providers.Object(controllers)
    get_services = providers.Object(services)
