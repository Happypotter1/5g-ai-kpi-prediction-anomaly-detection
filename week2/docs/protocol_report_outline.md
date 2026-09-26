# Week 2 5G 核心协议分析报告提纲

1. 实验环境：free5GC、UERANSIM、tcpdump、Wireshark。
2. 数据采集：N2 SCTP/38412、N3 UDP/2152、ICMP。
3. UE 注册：Initial UE Message / Registration Request。
4. 鉴权：Authentication Request / Response，RAND、AUTN、RES。
5. 安全：Security Mode Command / Complete；5G-EA0、128-5G-IA2。
6. Initial Context Setup 与 Allowed NSSAI（SST=1、SD=010203）。
7. PDU Session Resource Setup：PDU Session ID=1、UPF N3=10.0.2.15、TEID=0x00000006。
8. GTP-U：外层 10.200.200.2 → 10.0.2.15，内层 10.60.0.2 → 8.8.8.8。
9. 结论：控制面与用户面闭环验证。

