import grpc


def check_if_grpc_channel_is_active(channel: grpc.Channel, timeout_seconds: int = 5) -> bool:
    try:
        grpc.channel_ready_future(channel).result(timeout=timeout_seconds)
        return True
    except grpc.FutureTimeoutError:
        return False


def check_if_host_has_active_grpc_insecure_channel_server(host_address_with_port: str,
                                                          timeout_seconds: int = 5) -> bool:
    with grpc.insecure_channel(host_address_with_port) as channel:
        output = check_if_grpc_channel_is_active(channel, timeout_seconds)
    return output
