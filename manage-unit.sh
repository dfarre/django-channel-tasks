#!/bin/bash
URI="$1"; shift;
curl --unix-socket /var/run/control.unit.sock "$@" "http://localhost/${URI}"
