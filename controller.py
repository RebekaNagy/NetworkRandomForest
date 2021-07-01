import argparse
import grpc
import os
import sys
from time import sleep
import pandas as pd
import numpy as np
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestClassifier
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'utils/'))
import p4runtime_lib.bmv2
from p4runtime_lib.switch import ShutdownAllSwitchConnections
import p4runtime_lib.helper

class TableEntry:
   def __init__(self, table_name, match_fields=None, action_name=None, action_params=None):
    self.table_name     = table_name
    self.match_fields   = match_fields
    self.action_name    = action_name
    self.action_params  = action_params

def readDataset():
  train = pd.read_csv('titanic_training.csv', sep=";")
  train.Fare = train.Fare.astype(int)
  train.Age = train.Age.astype(int)
  train.Sex = np.where(train.Sex == 'male', 1, 0)

  return train

def traingingModel(xTrain, xTest, yTrain, yTest, max_tree, max_depth):
  model = RandomForestClassifier(max_depth=max_depth, n_estimators=max_tree)
  model.fit(xTrain, yTrain)
  print(model)
  print(model.score(xTest, yTest))

  return model

def getFeatures(train):
  modelFeatures = []
  for t in train.drop(train.columns[[0,1]], axis=1):
    modelFeatures.append(t)

  return modelFeatures

def featureConvertToNumber(feature):
  switcher = {
    "Age":      0,
    "Sex":      1,
    "Pclass":  	2,
    "Fare":     3
  }
  
  return switcher.get(feature)

def treeConvertToTableEntry(clf, modelFeatures, port):
  n_nodes = clf.tree_.node_count
  children_left = clf.tree_.children_left
  children_right = clf.tree_.children_right
  feature = clf.tree_.feature
  threshold = clf.tree_.threshold
  
  tableEntries = []
  tableEntries.append(TableEntry(
          "MyIngress.depth_0",
          {
            "nodeid"  : int(0),
            "nodebool": int(0)
          },
          "MyIngress.decision",
          {
            "next": int(1),
            "feat": int(featureConvertToNumber(modelFeatures[feature[0]])),
            "thr": int(np.ceil(threshold[0]).astype(int)),
            "depth": int(1)
          }
        ))

  stack = [(0, 1, 0, 0)]
  while len(stack) > 0:
    node_id, depth, parent, result = stack.pop()

    is_split_node = children_left[node_id] != children_right[node_id]

    if is_split_node:
      stack.append((children_left[node_id], depth + 1, node_id + 1, 0))
      stack.append((children_right[node_id], depth + 1, node_id + 1, 1))

      if threshold[children_right[node_id]] >= 0:
	      tableEntries.append(TableEntry(
	          "MyIngress.depth_" + str(depth),
	          {
	            "nodeid"  : int(node_id + 1),
	            "nodebool": int(1)
	          },
	          "MyIngress.decision",
	          {
	            "next": int(children_right[node_id]+1),
	            "feat": int(featureConvertToNumber(modelFeatures[feature[children_right[node_id]]])),
	            "thr": int(np.ceil(threshold[children_right[node_id]]).astype(int)),
	            "depth": int(depth + 1)
	          }
	        ))
      
      if threshold[children_left[node_id]] >= 0:
	      tableEntries.append(TableEntry(
	          "MyIngress.depth_" + str(depth),
	          {
	            "nodeid"  : int(node_id + 1),
	            "nodebool": int(0)
	          },
	          "MyIngress.decision",
	          {
	            "next": int(children_left[node_id]+1),
	            "feat": int(featureConvertToNumber(modelFeatures[feature[children_left[node_id]]])),
	            "thr": int(np.ceil(threshold[children_left[node_id]]).astype(int)),
	            "depth": int(depth + 1)
	          }
	        ))
    else:
      value = clf.tree_.value[node_id][0]
      prediction = 0
      if value[1] >= value[0]:
        prediction = 1

      tableEntries.append(TableEntry(
          "MyIngress.forward",
          {
            "nodeid"  : int(parent),
            "nodebool": int(result)
          },
          "MyIngress.packet_forward",
          {
            "port": int(port),
          	"result": int(prediction)
          }
        ))
            
  return tableEntries

def writeTunnelRules(p4info_helper, sw, tableEntries):
  for tableEntry in tableEntries:
    table_entry = p4info_helper.buildTableEntry(tableEntry.table_name, match_fields=tableEntry.match_fields, action_name=tableEntry.action_name, action_params=tableEntry.action_params)
    sw.WriteTableEntry(table_entry)

def readTableRules(p4info_helper, sw):
  print ('\n----- Reading tables rules for %s -----' % sw.name)
  for response in sw.ReadTableEntries():
    for entity in response.entities:
      entry = entity.table_entry
      table_name = p4info_helper.get_tables_name(entry.table_id)
      print ('%s: ' % table_name),
      for m in entry.match:
        print (p4info_helper.get_match_field_name(table_name, m.field_id))
        print ('%r' % (p4info_helper.get_match_field_value(m),))
      action = entry.action.action
      action_name = p4info_helper.get_actions_name(action.action_id)
      print ('->', action_name)
      for p in action.params:
        print (p4info_helper.get_action_param_name(action_name, p.param_id))
        print ('%r' % p.value)
      print()

def printGrpcError(e):
  print ("gRPC Error:", e.details())
  status_code = e.code()
  print ("(%s)" % status_code.name)
  traceback = sys.exc_info()[2]
  print ("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))

def main(p4info_file_path, bmv2_file_path, tableEntries):
  p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

  try:
    switches = []
    
    for i in range(5):
      switches.append(
        p4runtime_lib.bmv2.Bmv2SwitchConnection(
        name='s' + str(i + 1),
        address='127.0.0.1:5005' + str(i + 1),
        device_id=i,
        proto_dump_file='logs/s' + str(i + 1) + '-p4runtime-requests.txt')
      )

    for sw in switches:
      print(sw.name)
      sw.MasterArbitrationUpdate()
      sw.SetForwardingPipelineConfig(p4info=p4info_helper.p4info, bmv2_json_file_path=bmv2_file_path)
    
    for i in range(len(tableEntries)):
      writeTunnelRules(p4info_helper, switches[i], tableEntries[i])

  except KeyboardInterrupt:
    print (" Shutting down.")
  except grpc.RpcError as e:
    printGrpcError(e)

  ShutdownAllSwitchConnections()

max_tree = 5
max_depth = 5
if len(sys.argv) == 3:
	max_tree = int(sys.argv[1])
	max_depth = int(sys.argv[2])
sys.argv = [sys.argv[0]]

train = readDataset()
print train
xTrain, xTest, yTrain, yTest = train_test_split(train.drop(train.columns[[0,1]], axis=1), train.Survived, test_size = 0.2)
model = traingingModel(xTrain, xTest, yTrain, yTest, max_tree, max_depth)
modelFeatures = getFeatures(train)
tableEntries = []

for i in range(len(model.estimators_) - 1):
	clf = model.estimators_[i]
	tableEntries.append(treeConvertToTableEntry(clf, modelFeatures, 2))

clf = model.estimators_[len(model.estimators_) - 1]
tableEntries.append(treeConvertToTableEntry(clf, modelFeatures, 3))

parser = argparse.ArgumentParser(description='P4Runtime Controller')
parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                    type=str, action="store", required=False,
                    default='./build/decisiontree.p4.p4info.txt')
parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                    type=str, action="store", required=False,
                    default='./build/decisiontree.json')
args = parser.parse_args()

if not os.path.exists(args.p4info):
    parser.print_help()
    print "\np4info file not found: %s\nHave you run 'make'?" % args.p4info
    parser.exit(1)
if not os.path.exists(args.bmv2_json):
    parser.print_help()
    print "\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json
    parser.exit(1)
main(args.p4info, args.bmv2_json, tableEntries)
