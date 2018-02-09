# Docker events exporter

*Docker events exporter* expose docker API events ([oom, start, …](https://docs.docker.com/engine/reference/commandline/events/#object-types)) to prometheus metrics.

## Summary

[node-problem-detector](https://github.com/kubernetes/node-problem-detector)
doesn't expose the pod name, but only show events using logs files. In case of
OOM is not very helpful, *Docker events exporter* use docker API to retrieve
pod, container and namespace.

## Run on kubernetes as daemonsets

You can apply this ds on our cluster, in order to expose API events as
prometheus metrics.

```json
{
  "apiVersion": "extensions/v1beta1",
  "kind": "DaemonSet",
  "metadata": {
    "name": "events-notifier",
    "namespace": "inf"
  },
  "spec": {
    "updateStrategy": {
      "type": "RollingUpdate"
    },
    "template": {
      "metadata": {
        "labels": {
          "name": "events-notifier"
        },
        "annotations": {
          "prometheus.io/scrape": "true",
          "prometheus.io/port": "9000"
        }
      },
      "spec": {
        "containers": [
          {
            "name": "events-notifier",
            "image": "clustree:docker-events-exporter",
            "imagePullPolicy": "Always",
            "resources": {
              "requests": {
                "cpu": "0.1"
              },
              "limits": {
                "memory": "20Mi",
                "cpu": "0.3"
             }
            },
            "volumeMounts": [
              {
                "name": "dockersock",
                "mountPath": "/var/run/docker.sock"
              }
            ],
            "ports": [
              {
                "name": "prometheus",
                "containerPort": 9000
              }
            ]
          }
        ],
        "volumes": [
          {
            "name": "dockersock",
            "hostPath": {
              "path": "/var/run/docker.sock"
            }
          }
        ]
      }
    }
  }
}

```

And then fetch events on port `9000`

```bash
❯ curl 10.252.8.147:9000
# HELP docker_events Docker events
# TYPE docker_events counter
docker_events{env="int2",event="exec_start: bash",pod="ldap"} 1.0
docker_events{env="int2",event="oom",pod="ldap-2246486038-30nc1"} 1.0
```

## Prometheus alerts ?

Then you can imagine to configure prometheus alerts based on thoses metrics,
for example about OOM events…

```
groups:
- name: host_health
  - alert: oom
    expr: rate(docker_events{event="oom",kubernetes_namespace="inf"}[1m]) > 0
    labels:
      routing: slackonly
    annotations:
      link: '{{ $labels.event }} - {{ $labels.env }} - {{ $labels.pod }}'
```
