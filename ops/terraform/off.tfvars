# Between sessions. Scales the fleet to nothing; the Fargate services and the
# load balancer keep running for about $0.11/hr, which is the price of leaving
# the dashboard up.
worker_instances = 0
worker_replicas  = 0
