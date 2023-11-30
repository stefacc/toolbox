## get info about cluster
```
kubectl --kubeconfig=config get all
```
## get info about cluster
```
kubectl --kubeconfig=config cluster-info
```
## get info about services
```
kubectl --kubeconfig=config get services
or
kubectl --kubeconfig=config describe services
```
## get info about endpoints
```
kubectl --kubeconfig=config get endpoints
```
## get auto-scaler settings and status
```
kubectl --kubeconfig=config get hpa
```
## get info about deployment
```
kubectl --kubeconfig=config get deployment
```
## get info about pod
```
kubectl --kubeconfig=config get pods
```
## get info about pod with nodes
```
kubectl --kubeconfig=config get pods -o wide
```
## get more info about pod
```
kubectl --kubeconfig=config describe pod
```
## get ENV from specific pod
```
kubectl --kubeconfig=config exec "POD" -- printenv
```
## get ENV from specific container
```
kubectl --kubeconfig=config exec "POD" -c "CONTAINER" -- printenv
```
## get log of output stdout from a specific container
```
kubectl --kubeconfig=config log "POD" -c "CONTAINER" > file.log  
```
## copy file from local to container or pod
```
kubectl cp --kubeconfig=config <local-file> <some-namespace>/<some-pod>:<remote-file> -c <container>
```
## show resources by containers
```
kubectl --kubeconfig=config top pod "POD" --containers
```
## check specific service
```
kubectl --kubeconfig=config get service/"NAME"
or
kubectl --kubeconfig=config describe service "NAME"
```
## show configmap or secrets
```
kubectl --kubeconfig=config get configmap
kubectl --kubeconfig=config describe configmap

kubectl --kubeconfig=config get secrets --all-namespaces
kubectl --kubeconfig=config get secret
kubectl --kubeconfig=config describe secret
```
## go in a container in a pod
```
kubectl --kubeconfig=config exec "POD" -c "CONTAINER" -it -- bash
```
## show all containers
```
kubectl --kubeconfig=config get pods "POD" -o jsonpath='{.spec.containers[*].name}' 
or
kubectl --kubeconfig=config describe pod/"POD" -n "NAMESPACE"
```
## get events from pod
```
kubectl --kubeconfig=config get events
```
## show list of nodes
```
kubectl --kubeconfig=config get nodes
```
## delete pod
```
kubectl delete pods <POD> --grace-period=0
```
