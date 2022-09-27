import pyVim
from pyVim import connect
from pyVmomi import vim
import time
import multiprocessing
import subprocess
l=time.localtime(time.time())

def spawn(vcenter):
        fn_h=vcenter+"_h"
        fn_v=vcenter+"_v"
        user="readonlyuser@vsphere.local"
        P='xxx'
        try:
                my_cluster = connect.ConnectNoSSL(vcenter, 443, user, P)
                content = my_cluster.RetrieveContent()
                hosts = vmhosts(content)
                printIP(hosts,fn_h,vcenter)
                get_vm(content,fn_v)
                connect.Disconnect(my_cluster)
        except:
                f=open(fn_h,"w")
                L1="err --> "+vcenter+"\n"
                f.write(L1)

def vmhosts(content):
        host_view = content.viewManager.CreateContainerView(content.rootFolder,[vim.HostSystem],True)
        obj = [host for host in host_view.view]
        host_view.Destroy()
        return obj

def GetHostSw(hosts,v1):
        hostSW = {}
        f=open(fn_h,"a")
        for host in hosts:
                try:
                        sw = host.config.network.vswitch
                        hostSW[host] = sw
                except:
                        linie = host.name+" Error\n"
                        f.write(linie)
        f.close()
        return hostSW

def printHost(h):
        print "Hosts"
        print "----"
        for i in h:
                print str(i.name)+"|"+str(i.hardware.biosInfo.biosVersion)+"|"+str(i.hardware.biosInfo.releaseDate.year).strip()+"-"+str(i.hardware.biosInfo.releaseDate.month).strip()+"-"+str(i.hardware.biosInfo.releaseDate.day).strip()

def printSW(h1):
        hostSwitchDict = GetHostSw(h1)
        for h,v in hostSwitchDict.items():
                for i in v:
                        print i.name, h.name

def get_vmk_services(h):
        d={}
        for i in h.configManager.virtualNicManager.info.netConfig:
                if i.selectedVnic != []:
                        for j in i.candidateVnic:
                                if j.device==i.selectedVnic[0].decode('utf-8', 'ignore').split("Nic-")[1]:
                                        if j.device not in d.keys():
                                                d[j.device]=[]
                                        d[j.device].append(i.nicType)
        return d

def printIP(hosts,fn,v1):
        s='|'
        f=open(fn,"a")
        hostSwitchDict = GetHostSw(hosts,v1)
        for i in hostSwitchDict.items():
                d = get_vmk_services(i[0])
                for v in i[0].config.network.vnic:
                        l1=v1+s+i[0].name+s+v.device+s+v.spec.ip.ipAddress+s+v.spec.mac+s+str(v.spec.mtu)+s+v.portgroup+s+i[0].runtime.connectionState
                        if v.device in d.keys():
                                if len(d[v.device])>1:
                                        l1=l1+s
                                        for d1 in d[v.device]:
                                                l1=l1+d1
                                                if d[v.device].index(d1)<len(d[v.device])-1:
                                                        l1=l1+","
                        l1=l1+'\n'
                        f.write(l1)
        f.close()

def get_vm(content,fn):
        container = content.rootFolder
        vt = [vim.VirtualMachine]
        cnt_v = content.viewManager.CreateContainerView(container,vt,True)
        children = cnt_v.view
        f=open(fn,"a")
        for i in children:
                l1=''
                try:
                        l1=i.summary.config.name+"|"+str(i.summary.config.guestId)+'|'+i.summary.runtime.host.name+'|'+str(i.summary.config.numCpu)+'|'+str(i.summary.config.memorySizeMB)+'MB|'+str(i.summary.guest.ipAddress)+'|'+i.summary.runtime.powerState
                except:
                        pass
                try:
                        a=i.storage.perDatastoreUsage[0].datastore.name
                        l1=l1+'|'+a
                except:
                        pass
                try:
                        a=i.storage.perDatastoreUsage[0].datastore.summary.type
                        l1=l1+'|'+a
                except:
                        pass
                l1=l1+"\n"
                f.write(l1)
                for j in i.guest.net:
                        if len(j.ipAddress)>0:
                                l2 = i.summary.config.name+"|"+j.ipAddress[0]+"|"+str(j.network)+"|"+str(j.macAddress)+'\n'
                                f.write(l2)

def se_vm(c,ip):
        searcher = c.content.searchIndex
        vm = searcher.FindByIp(ip=ip, vmSearch=True)
        try:
                print vm.config.name
        except:
                print "not found"

def get_fn():
        fn=str(l.tm_year)+"_"+str(l.tm_mon)+"_"+str(l.tm_mday)+"_"+str(l.tm_hour)+"_"+str(l.tm_min)+"_"+str(l.tm_sec)
        return fn

vc=["v1.local","v2.local","v3.local"]
fn_v="vms_"+get_fn()
fn_h="hosts_"+get_fn()
pool = multiprocessing.Pool(processes=len(vc))
results = [pool.apply_async(spawn, args=(x,)) for x in vc]
output = [p.get() for p in results]
c1=subprocess.Popen("cat *_v > "+fn_v, shell=True, stdout=subprocess.PIPE).stdout.read()
c1=subprocess.Popen("cat *_h > "+fn_h, shell=True, stdout=subprocess.PIPE).stdout.read()
c1=subprocess.Popen("rm *_h", shell=True, stdout=subprocess.PIPE).stdout.read()
c1=subprocess.Popen("rm *_v", shell=True, stdout=subprocess.PIPE).stdout.read()
