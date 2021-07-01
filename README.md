# Minimalist RandomForest in P4

## Setting up the environment

The project was implemented in the P4 Tutorial Virtual Machine. Additionally we need to install two libraries for the training part of the algorithm.
> sudo apt-get install python-pandas
> sudo apt-get install python-sklearn

## Running the program

First, in the directory of the project, we need to build our Mininet. 
> make 

This command will build the program, and set up the network with the corresponding topology.\

After this, in a separate terminal we should run the controller.py file.
> python ./controller.py

This is the Control Plane of the network. We can add two number parameters(maximum number of decision trees[1,5], maximum depth of trees [2,5])(default 5 5)\

If the controller is done, we can start to send packages between the two hosts. We should write the next command in the terminal of the Mininet to achieve this.
> xterm h1 h2

Two new terminal should appear on the screen.\

We have to start the receive.py script on the second host(h2).
> python ./receive.py

With this the h2 host will begin to listen for incoming packets.\

Now we can send our packets to the network. In the first host(h1) run the randomforest.py script.
> python ./randomforest.py

The host should start to send the packets to the network, and we should see them arrive on the other host.

## About the program

### Network
```
h1 -- s1 -- s2 -- s3 -- s4 -- s5
       |_____|_____|_____|_____|
                   |
                   s6 -- h2
```
### Data plane
We define two different P4 programs. The decisiontree.p4 will be installed on the first five switch, while the sixth switch will have the prediction.p4 file.\
The desiciontree.p4 represents a single decision tree in the forest. Every level of the tree translates into a table in the pipeline. The maximum depth of a tree is 5 
since we only defined five tables in the program. The tables use one action, witch decides about the next node in the tree. \
The intermediate nodes correspond to the depth_i (i:[0,4]) tables, while the leaf nodes correspond to the forward table. The latter does not call the decision action, but the packet_forward action, which, in addition to saving the prediction of the actual tree in the header, also sets the appropriate port for forwarding the packet. \
Packets will pass through up to as many switches as we set for the maximum number of trees. This means that if we set three in the parameter, the packet will go to the sixth after the first three switches, omitting the fourth and fifth switches. By default, packets are processed on all switches. \
For the purpose of checking, we use the counter and depth fields in the packets to keep track of how many switches the packet went through and the maximum depth in the trees according to the specified maximum parameters. \
In prediction.p4, i. e. the sixth switch, the prediction is set in the header based on a majority vote. When this is done, the packet is forwarded to the second host.

### Control plane
In the controller.py, the randomforest algorithm is first trained, using the more well-known titanic data set. Then, from the result of this, table entries are generated from the decision trees, and then these entries are written to the first 5 switches.

### Sending and receiving packets
The packets identify each person from the titanic dataset. For the packages we have created a custom header that contains helper counter fields(counter, depth) in addition to the person's data(id, age, sex, p_class, fare, survived), as well as a field that will contain the prediction(switch_survived).\
The sending script is contained in the randomforest.py file, while the receiving script is contained in the receive.py file.
