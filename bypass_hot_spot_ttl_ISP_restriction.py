import pydivert

with pydivert.WinDivert("outbound and ip") as w:
    print("TTL fix активен. TTL = 65")
    count = 0
    for packet in w:
        if packet.ipv4:
            old_ttl = packet.ipv4.ttl
            packet.ipv4.ttl = 65
            packet.recalculate_checksums()
            count += 1
            if count % 100 == 0:
                print(f"Обработано пакетов: {count}")
        w.send(packet)
