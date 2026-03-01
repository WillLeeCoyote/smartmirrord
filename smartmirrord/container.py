from dependency_injector import containers, providers

from smartmirrord.hardware.camera import Camera
from smartmirrord.hardware.ir_emulator import IREmulator
from smartmirrord.hardware.uart_transport import UartTransport
from smartmirrord.hardware.power_status import PowerStatus
from smartmirrord.services.power_service import PowerService
from smartmirrord.services.ir_service import IRService
from smartmirrord.services.motion_service import MotionService
from smartmirrord.services.uart_dispatcher import UartDispatcher
from smartmirrord.services.videomute_service import VideoMuteService
from smartmirrord.services.display_availability_service import DisplayAvailabilityService
from smartmirrord.services.display_policy_service import DisplayPolicyService


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    # Hardware Layer (Singletons)
    camera = providers.Singleton(Camera)
    ir_emulator = providers.Singleton(IREmulator)
    uart_transport = providers.Singleton(UartTransport)
    power_status = providers.Singleton(PowerStatus)

    # Core Services (Singletons with auto-wiring)
    power_service = providers.Singleton(PowerService, power_status=power_status)

    ir_service = providers.Singleton(IRService, ir_emulator=ir_emulator)

    motion_service = providers.Singleton(MotionService, camera=camera)

    uart_dispatcher = providers.Singleton(
        UartDispatcher,
        transport=uart_transport,
    )

    # Policy Services
    videomute_service = providers.Singleton(
        VideoMuteService,
        dispatcher=uart_dispatcher,
        uart=uart_transport,
        power_service=power_service,
    )

    display_availability_service = providers.Singleton(
        DisplayAvailabilityService,
        power_service=power_service,
        ir_service=ir_service,
    )

    display_policy_service = providers.Singleton(
        DisplayPolicyService,
        video_mute_service=videomute_service,
        motion_service=motion_service,
        power_service=power_service,
        remute_delay=config.display_policy_timeout,
        schedule_json=config.schedule_json,
    )

    # Explicit startup order (event sources → event consumers)
    startup_order = providers.List(
        power_service,
        motion_service,
        ir_service,
        uart_transport,
        uart_dispatcher,
        videomute_service,
        display_availability_service,
        display_policy_service,
    )


