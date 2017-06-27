#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Clustree <https://www.clustree.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import docker
from prometheus_client import start_http_server, Counter

APP_NAME = "Docker events prometheus exporter"
EVENTS = Counter('docker_events',
                 'Docker events',
                 ['event', 'pod', 'env'])


def print_timed(msg):
    to_print = '{} [{}]: {}'.format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'docker_events',
        msg)
    print(to_print)


def watch_events():
    client = docker.DockerClient(version='auto',
                                 base_url='unix://var/run/docker.sock')
    for event in client.events(decode=True):
        attributes = event['Actor']['Attributes']
        if event['Type'] == 'network':
            continue
        if 'io.kubernetes.docker.type' in attributes:
            if attributes['io.kubernetes.container.name'] == 'POD':
                continue
            if event['status'].startswith(('exec_create', 'exec_detach')):
                continue
            msg = '{} on {} ({})'.format(
                event['status'].strip(),
                attributes['io.kubernetes.pod.name'],
                attributes['io.kubernetes.pod.namespace'])
            print_timed(msg)
            pod = attributes['io.kubernetes.container.name']
            if event['status'] == 'oom':
                pod = attributes['io.kubernetes.pod.name']
            EVENTS.labels(event=event['status'].strip(),
                          pod=pod,
                          env=attributes['io.kubernetes.pod.namespace']).inc()


if __name__ == '__main__':
    print_timed('Start prometheus client on port 9000')
    start_http_server(9000, addr='0.0.0.0')
    try:
        print_timed('Watch docker events')
        watch_events()
    except docker.errors.APIError:
        pass
