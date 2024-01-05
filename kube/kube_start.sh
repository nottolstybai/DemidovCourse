minikube start

kubectl apply -f ./app
kubectl apply -f ./db

kubectl port-forward service/app 8080:8080