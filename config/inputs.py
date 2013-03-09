# import the inputs and an output
from flows import Fanin
from inputs.udp import Udp
from inputs.zeromq import Zeromq
from outputs.log import Log

# Multiple input sources can be simultaneously received. They are read in
# parallel and events 'fan in' to the rest of the pipeline.
with Fanin():
    Udp(port=6000)
    Zeromq()

# log the results to logcabin.log
Log()
