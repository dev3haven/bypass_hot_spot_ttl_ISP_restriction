Uses [pydivert](https://github.com/ffalcinelli/pydivert)

Changes [TTL](https://en.wikipedia.org/wiki/Time_to_live) to 65 for ipv4 and 129 for ipv6 for all WiFi Hot Spot Internet traffic to bypass [MNO](https://en.wikipedia.org/wiki/Mobile_network_operator) or [ISP](https://en.wikipedia.org/wiki/ISP_(disambiguation)) restrictions.  
Local addresses are ignored by default.

Run as an **administrator**
```sh
pip install pydivert
python bypass_hot_spot_ttl_ISP_restriction.py
```
