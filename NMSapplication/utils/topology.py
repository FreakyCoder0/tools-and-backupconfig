from NMSapplication.models import Launchscheduler,Scheduler
from django.core.mail import send_mail
from NMSproject import settings
# from json import dumps, loads
import json
from collections import OrderedDict
import networkx as nx
import struct
import socket
import pandas as pd
import ipaddress
from os import path
# from django.conf import settings
try:
   from pysnmp.hlapi import *
except Exception as e:
   pass
from datetime import datetime
import re
import struct
import socket
from os import path
try:
   from pysnmp.hlapi import *
except Exception as e:
   pass
import fnmatch 



class DiscoverTopology:
   cdp_base = '1.3.6.1.4.1.9.9.23.1.2.1.1' #cdpCacheTable
   lldp_base = '1.0.8802.1.1.2.1.4.1.1' #lldpRemEntry

   def __init__(self, task_id):
      self.task_id = task_id
      self.log_messages = {}
      self.seed_ip = '192.168.100.51'
      self.community = 'public'
      self.port = '161' 
      self.authData = CommunityData(self.community, mpModel=1) 
      self.topology = OrderedDict()
      self.protocol = 'lldp'

   def is_valid_ip(ip):
      try:
         socket.inet_aton(ip)
         return True
      except socket.error:
         return False

   def hex_to_ip(hex_str):
      return socket.inet_ntoa(struct.pack(">L",int(hex_str,16)))

   def snmp_query(community, ip, oid):
      result = {}
      iterator = nextCmd(SnmpEngine(),
                        CommunityData(community),
                        UdpTransportTarget((ip, 161)),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)),
                        lexicographicMode=False)

      for errorIndication, errorStatus, errorIndex, varBinds in iterator:
         if errorIndication or errorStatus:
               print(f"Error: {errorIndication or errorStatus.prettyPrint()}")
               break

         for varBind in varBinds:
               result[str(varBind[0])] = varBind[1].prettyPrint()

      return result

   def check_lldp_cdp_enabled(community, ip):
      cdp_enabled = 0
      lldp_enabled = 0

      cdp_data = DiscoverTopology.snmp_query(community, ip, f'{DiscoverTopology.cdp_base}.6')
      lldp_data = DiscoverTopology.snmp_query(community, ip, f'{DiscoverTopology.lldp_base}.9')

      if len(cdp_data):
         cdp_enabled = 1
      if len(lldp_data):
         lldp_enabled = 1

      return cdp_enabled, lldp_enabled
      
   def get_make_model(make_model):	
      #check if its hex value, convert to string
      if make_model[:2] == '0x':
         make_model = bytes.fromhex(make_model[2:]).decode()
      words = make_model.split(',')
      #print(make_model)
      if len(words) >= 2:
         if ',' in make_model:
               vendor = words[0]
               model = words[1].strip()
               if 'Software' in vendor and 'Software' not in model:
                  #print("===>", vendor.split())
                  vendor = vendor.split()[0]
                  model = vendor.split()[0]
               if 'Software' in model:
                  model = model.split()[0]
               #print("1", "\"",make_model,"\"", model, vendor)
         else:
               vendor = words[0]
               model = ' '.join(words[1:])
               #print("2", "\"", make_model, "\"",model, vendor)
      else:
         split_result = make_model.split(' ')
         if len(split_result) > 1:
               model = split_result[1]
               vendor = split_result[0]
               #print("3", "\"", make_model, "\"", model, vendor)
         else:
               model = split_result[0]
               vendor = ''
               #print("4", "\"", make_model, "\"", model, vendor)
      
      return [model.strip(), vendor.strip()]

   def network_discovery(seed_ip, community):
      devices = {}
      device_make = {}
      visited_devices = set()
      visited_ips = set()

      def discover_device(ip):
         if not DiscoverTopology.is_valid_ip(ip) or ip in visited_ips:
               return
         neighbor_ip = '' 
         print("Probing Device IP: ", ip)
         device_data = DiscoverTopology.snmp_query(community, ip, '1.3.6.1.2.1.1.5')
         if not device_data:
               return
         device_name = list(device_data.values())[0]
         if device_name in visited_devices:
               return
         else:
               visited_devices.add(device_name)
               visited_ips.add(ip)

         devices[device_name] = {'ip': ip, 'neighbors': {}}
         cdp, lldp = DiscoverTopology.check_lldp_cdp_enabled(community, ip)
         if cdp:
               cdp_base = '1.3.6.1.4.1.9.9.23.1.2.1.1'
               neighbour_ip = 'not advertised'
               neighbor_ip_value = ''
               
               neighbor_ip_oid = f'{cdp_base}.4'
               neighbor_name_oid = f'{cdp_base}.6'
               neighbor_port_oid = f'{cdp_base}.7'
               localInterface_base = '1.3.6.1.2.1.2.2.1.2' #ifDescr
               neighbor_platform_oid = f'{cdp_base}.8'

               neighbor_ips = DiscoverTopology.snmp_query(community, ip, neighbor_ip_oid)
               neighbor_names = DiscoverTopology.snmp_query(community, ip, neighbor_name_oid)
               neighbor_ports = DiscoverTopology.snmp_query(community, ip, neighbor_port_oid)
               local_Interfaces = DiscoverTopology.snmp_query(community, ip, localInterface_base)
               device_model = DiscoverTopology.snmp_query(community, ip, neighbor_platform_oid)
               #print(neighbor_ips,neighbor_names, neighbor_ports, local_Interfaces)

               for oid, neighbor_name in neighbor_names.items():
                  remoteIndex = oid.split('.')[-1]
                  localIndex = oid.split('.')[-2]
                  neighbor_interface = neighbor_ports.get(f'{cdp_base}.7.{localIndex}.{remoteIndex}', '')
                  neighbor_ip_value = neighbor_ips.get(f'{cdp_base}.4.{localIndex}.{remoteIndex}', '')
                  local_interface = local_Interfaces.get(f'{localInterface_base}.{localIndex}', '')

                  #get make model of the neighbor
                  make_model = device_model.get(f'{cdp_base}.8.{localIndex}.{remoteIndex}')
                  
                  if len(make_model.split()) == 1:
                     device_make[neighbor_name] = ['',make_model.split()[0]]
                  elif len(make_model.split()) == 2:
                     device_make[neighbor_name] = [make_model.split()[1],make_model.split()[0]]

                  neighbor_ip_value = DiscoverTopology.hex_to_ip(neighbor_ip_value)
                  #print(neighbor_name, local_interface, neighbor_ip_value, neighbor_interface)
                  if neighbor_ip_value:
                     if neighbor_name in devices[device_name]['neighbors'].keys():
                           #Multiple Link for to same device
                           devices[device_name]['neighbors'][neighbor_name].append( {
                              'ip': neighbor_ip_value,
                              'localInt': local_interface,
                              'remotePort' : neighbor_interface
                              })
                     else:
                           devices[device_name]['neighbors'][neighbor_name] = [{
                              'ip': neighbor_ip_value,
                              'localInt': local_interface,
                              'remotePort' : neighbor_interface
                              }]
                  discover_device(neighbor_ip_value)

         if lldp:
               lldp_base = '1.0.8802.1.1.2.1.4.1.1' #lldpRemEntry
               localInterface_base = '1.3.6.1.2.1.2.2.1.2' #ifDescr
               neighbourIP_base = '1.0.8802.1.1.2.1.4.2.1' #lldpRemManAddrEntry
               neighbor_ip_value = ''

               neighbor_names = DiscoverTopology.snmp_query(community, ip, f'{lldp_base}.9') #lldpRemSysName
               neighbor_ports = DiscoverTopology.snmp_query(community, ip, f'{lldp_base}.7')
               local_Interfaces = DiscoverTopology.snmp_query(community, ip, f'{localInterface_base}')
               neighbor_ips = DiscoverTopology.snmp_query(community, ip, f'{neighbourIP_base}.2') #lldpRemManAddr
               device_model = DiscoverTopology.snmp_query(community, ip, f'{lldp_base}.10')
               remoteChassisId = DiscoverTopology.snmp_query(community, ip, f'{lldp_base}.5')

               if len(neighbor_ips): #oid exists in device
                  ipFlag =  'lldpRemManAddr'
               else:
                  neighbor_ips = DiscoverTopology.snmp_query(community, ip, f'{neighbourIP_base}.4') #lldpRemManAddrIfId, oid has the IP address
                  if len(neighbor_ips):
                     ipFlag = 'lldpRemManAddrIfId'
                  else:
                     ipFlag = None
               #print(neighbor_ips, ipFlag)
               for oid, neighbor_name in neighbor_names.items():
                  neighbor_ip_value = 'not advertised' #initialize
                  ip_oid_suffix = "xxxx" #initialize for debug
                  remoteIndex = oid.split('.')[-1] #Last digit of OID represents Remote Interface Index
                  localIndex = oid.split('.')[-2] # Second to last digit of OID represents Local Interface Index
                  #condition Mikrotek, if Second to last digit of OID represents is 0 Local Interface Index, will also be the last digit of oid
                  if localIndex == '0':
                     _localIndex = oid.split('.')[-1]
                  local_interface = local_Interfaces.get(f'{localInterface_base}.{localIndex}', '')
                  ip_oid_suffix = oid[len(f'{lldp_base}.9'):].lstrip('.') #anything extra after lldpRemSysName is suffix for mgmtt IP addr
                  #neighbor_interface = neighbor_ports.get(f'{lldp_base}.7.{localIndex}.{remoteIndex}', '')
                  neighbor_interface = neighbor_ports.get(f'{lldp_base}.7.{ip_oid_suffix}', '')
                  make_model = device_model.get(f'{lldp_base}.10.{ip_oid_suffix}', ' , ')

                  #for End devices where neighbour name is null, get chassis Id
                  if not neighbor_name:
                     neighbor_name = remoteChassisId.get(f'{lldp_base}.5.{ip_oid_suffix}', 'unknown')

                  device_make[neighbor_name] = DiscoverTopology.get_make_model(make_model)

                  if ipFlag == 'lldpRemManAddr':
                     #exact match, ip is in dict value
                     pattern = f'{neighbourIP_base}.2.{ip_oid_suffix}'
                     neighbor_ip_value = neighbor_ips.get(pattern, '')
                  elif ipFlag == 'lldpRemManAddrIfId':
                     pattern = f'{neighbourIP_base}.4.{ip_oid_suffix}.*'
                     match = fnmatch.filter(list(neighbor_ips), pattern)
                     if len(match):
                           # Extract the IP address from oid using regular expression by periods (.) and colons (:) for IPV4 and IPV6 respectively
                           neighbor_ip_value = re.search(r"\d{1,3}(?:\.\d{1,3}){3}$", match[0]).group()
                  else:
                     neighbor_ip_value = 'not advertised'
                  
                  #neighbor_ip_value = hex_to_ip(neighbor_ip_value)

                  #print(neighbor_name, local_interface, neighbor_interface, ",",neighbor_ip_value)
                  if neighbor_ip_value:
                     if neighbor_name in devices[device_name]['neighbors'].keys():
                           #Multiple Link for to same device
                           devices[device_name]['neighbors'][neighbor_name].append( {
                              'ip': neighbor_ip_value,
                              'localInt': local_interface,
                              'remotePort' : neighbor_interface
                              })
                     else:
                           devices[device_name]['neighbors'][neighbor_name] = [{
                              'ip': neighbor_ip_value,
                              'localInt': local_interface,
                              'remotePort' : neighbor_interface
                              }]
                     discover_device(neighbor_ip_value)

      discover_device(seed_ip)
      #print(json.dumps(device_make, indent=4))
      for device_name in devices.keys():
         if device_make.get(device_name, ''):
               devices[device_name]['make'] = device_make[device_name][1]
               devices[device_name]['model'] = device_make[device_name][0]
         else:
               devices[device_name]['make'] = 'unknown'
               devices[device_name]['model'] = 'unknown'
      return devices

   def main(self):
      discovered_devices = DiscoverTopology.network_discovery(self.seed_ip, self.community)
      created = Launchscheduler.objects.create(
            task_id=self.task_id,
            scheduler_type='TopologyDiscovery',
            logs=json.dumps(discovered_devices, indent=4)
      )
      email_subject = Scheduler.objects.filter(scheduler_type='TopologyDiscovery').last()
      send_mail( 
               subject = email_subject.email_subject, 
               message = json.dumps(discovered_devices, indent=4), 
               from_email = settings.EMAIL_HOST_USER, 
               recipient_list=['poasharshtestmail@gmail.com']
      )