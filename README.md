Supports **Windows** and **Linux**.  
Does not support **Android**, for **Android** probbaly you need to have **root**.  
Uses [pydivert](https://github.com/ffalcinelli/pydivert)

Changes [TTL](https://en.wikipedia.org/wiki/Time_to_live) to 65 for ipv4 and 129 for ipv6 for all WiFi Hot Spot Internet traffic to bypass [MNO](https://en.wikipedia.org/wiki/Mobile_network_operator) or [ISP](https://en.wikipedia.org/wiki/ISP_(disambiguation)) restrictions.  
Local addresses are ignored by default.

### Install

```sh
git clone https://github.com/dev3haven/bypass_hot_spot_ttl_ISP_restriction.git
cd bypass_hot_spot_ttl_ISP_restriction
pip install pydivert pyyaml
```

### Run
Just run **start.bat** for Windows or **start.sh** for Linux.  
Or execute the command below manually.
```sh
python ttl_gui.py
```
Addionally for Linux you need to give rights
```sh
chmod +x start.sh
```
