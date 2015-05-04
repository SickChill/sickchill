#!/bin/sh
openssl s_server -www -cert pki/localhost.crt -key pki/localhost.key -accept 4443
