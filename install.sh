juju destroy-model indicodepl --force -y --destroy-storage
charmcraft pack
juju add-model indicodepl
juju deploy ./indico_ubuntu-20.04-amd64.charm --resource indico-image=localhost:32000/indico3:latest --resource indico-nginx-image=localhost:32000/indico-nginx:latest
juju deploy postgresql-k8s --channel=latest/stable --series=focal
juju deploy redis-k8s redis-broker
juju deploy redis-k8s redis-cache
juju relate redis-broker indico
juju relate redis-cache indico
juju relate indico postgresql-k8s:db
juju debug-log --replay
