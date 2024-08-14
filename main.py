import asyncio
import socket as s

host = input("Host: ")
ports = input("Port(s): ").split(" ")

threads = 1

async def loadMsg(so: s.socket, m_tries: int = 20) -> bytes:
    msg = b""
    tries = 0
    while tries < m_tries:
        try:
            buf = so.recv(1024)
            if buf:
                msg += buf
                tries = 0
            else:
                tries += 1
        except BlockingIOError:
            if msg != b"":
                tries += 7
                await asyncio.sleep(0.05)
            else:
                tries += 1
                await asyncio.sleep(0.1)
    return msg


async def handle(client: s.socket, addr: tuple[str, int], port):
    global threads
    t = str(threads)
    threads += 1
    loop = asyncio.get_running_loop()

    client.setblocking(False)

    chost, cport = addr
    chost_b, host_b = chost.encode(), host.encode()
    print(f"Started Thread {t}: {chost}:{cport} -> {host}:{port}")

    server = s.socket(s.AF_INET, s.SOCK_STREAM)
    server.connect((host, port))
    server.setblocking(False)

    while True:
        msg = await loadMsg(client)
        msg = msg.replace(chost_b, host_b)

        if not msg:
            print(f"Thread {t} Closed by Server\n")
            break
        try:
            print(t + " Client: " + msg.decode().replace("\n", "\n          "))
        except UnicodeDecodeError:
            print(t + " Client: UnicodeDecodeError 😬")

        await loop.sock_sendall(server, msg)

        msg = await loadMsg(server)

        if not msg:
            print(f"Thread {t} Closed by Client\n")
            break
        try:
            print(t + " Server: " + msg.decode().replace("\n", "\n          "))
        except UnicodeDecodeError:
            print(t + " Server: UnicodeDecodeError 😬")

        await loop.sock_sendall(client, msg)


async def run_server(port: int):
    loop = asyncio.get_running_loop()
    server = s.socket(s.AF_INET, s.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen()
    server.setblocking(False)

    while True:
        client, addr = await loop.sock_accept(server)
        await loop.create_task(handle(client, addr, port))


async def main():
    tsks = []
    for p in ports:
        tsks.append(asyncio.create_task(run_server(int(p))))
        print(f"Now you can connect your client to 127.0.0.1:{p}")

    print("\n")
    await asyncio.gather(*tsks)


asyncio.run(main())
