# l2fwd

We got l2fwd app from dpdk version 19.08 and we extended the app with empty/full poll metrics
(following l3fwd-power's source code extensions).

We also created a python script based on usertools/dpdk-telemetry-client.py of dpdk to collect the desired metrics.

A flask server is provided to expose these metrics.

