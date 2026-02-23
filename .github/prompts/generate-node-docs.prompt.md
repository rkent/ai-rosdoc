---
name: Generate Node Documentation
description: Run this to generate or update documentation on any nodes found in the workspace.
agent: 'agent'
---

Locate all ros2 nodes in both python and c++ files in the current directory. Prepare documentation for each node. The documentation should be in a folder doc/Nodes/ relative to the package.xml file for each ros2 package. There should be one .md markdown file per node, with the name of the file matching the node name. Documentation for the node should include:

- node name
- after the node name, in italics 'This file is ai generated and may contain mistakes. If you edit this file, remove this notice to prevent rewriting by ai.'
- node description
- subscriptions, publishers, services, and actions for the node with interface (e.g.message) type.
- **IMPORTANT: ONLY include sections (## Publishers, ## Subscribers, ## Services, ## Actions) if the node actually has items of that type. DO NOT include empty sections or sections with "None". Omit the entire section if there are no items.**
- documentation of any parameters defined for the node.
- example of how to run the node using the ros2 run command.

Additional instructions:
- if the default value is a C++ constant, find the literal value of that constant. Do no just show the constant name.
- if the documentation already exists, review it and update if appropriate. But do not modify the file if it contains the text "file is ai generated"

In addition to the markdown file, in the same directory create a .json file, with the name of the file matching the node name. The json file should match the following schema per https://json-schema.org/draft/2020-12/schema:
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "http://ros.org/schemas/node_doc.json",
  "donotmodify": "false",
  "name": {
    "type": "string",
    "description": "node name"
  },
  "summary": {
    "type": "string",
    "description": "a short description of the function of the node",
    "minLength": 30,
    "maxLength": 100
  },
  "overview": {
    "type": "string",
    "description": "a longer description of the function of the node",
    "minLength": 110,
    "maxLength": 300
  },
  "repo": {
    "type": "string",
    "description": "the name of the repository containing the node's package"
  },
  "package": {
    "type": "string",
    "description": "the name of the package containing the node"
  },
  "parameters": {
    "type": "array",
    "description": "ROS parameters for the node",
    "items": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "the identifier used to reference the parameter in the ROS API",
        },
        "type": {
          "type": "string",
          "description": "the type of the parameter, e.g. string, int, float"
        },
        "default": {
          "type": "string",
          "description": "the default value of the parameter, if any"
        },
        "summary": {
          "type": "string",
          "description": "a short description of the purpose of the parameter",
          "minLength": 20,
          "maxLength": 80
        }
      }
    }
  },
  "interfaces": {
    "type": "array",
    "description": "A list of the various interfaces implemented  by the node",
    "items": {
      "type": "object",
      "properties": {
        "itype": {
          "enum": ["publisher", "subscriber", "service", "client", "action server", "action client"],
          "description": "The type of ROS interface"
        },
        "topic": {
          "type": "string",
          "description": "the string used to reference the interface"
        },
        "mtype": {
          "type": "string",
          "description": "the message type that characterizes the interface"
        },
        "summary": {
          "type": "string",
          "description": "A short summary of the purpose of the interface",
          "minLength": 20,
          "maxLength": 80
        }
      }
    }
  }
}

If the json file already exists, and it contains a top-level field "donotmodify" with the value of "true", then do not change the json file. Otherwise, read the existing file and update it if needed to reflect the correct current values.
    
