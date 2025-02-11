# Cloud Run DNS Setup Guide

## Overview
This document outlines the configuration for connecting Cloud Run with a custom domain (swacktech.com) using direct DNS resolution.

## Cloud Run Configuration

### Domain Mapping
```yaml
apiVersion: domains.cloudrun.com/v1alpha1
kind: DomainMapping
metadata:
  name: swacktech.com
  namespace: default
spec:
  routeName: swacktech-frontend
```

### Service Configuration
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: swacktech-frontend
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/ingress-status: all
    run.googleapis.com/launch-stage: BETA
    run.googleapis.com/allow-unauthenticated: "true"
```

## DNS Configuration

### Cloudflare DNS Records
Set up the following A records in Cloudflare:

1. A Records (all with proxy status OFF - grey cloud):
   - @ -> 216.239.32.21
   - @ -> 216.239.34.21
   - @ -> 216.239.36.21
   - @ -> 216.239.38.21

2. AAAA Records (all with proxy status OFF - grey cloud):
   - @ -> 2001:4860:4802:32::15
   - @ -> 2001:4860:4802:34::15
   - @ -> 2001:4860:4802:36::15
   - @ -> 2001:4860:4802:38::15

### Cloudflare SSL/TLS Settings
1. SSL/TLS mode: Off (not secure)
2. Edge Certificates:
   - Always Use HTTPS: Disabled
   - Automatic HTTPS Rewrites: Disabled

## Verification
1. DNS propagation takes 5-10 minutes
2. Cloud Run certificate provisioning occurs automatically
3. Verify using:
   ```bash
   dig swacktech.com
   curl -v https://swacktech.com
   ```

## Scripts
The following scripts were created to manage the setup:

1. `setup_direct_dns.sh`: Main script for configuring DNS and domain mapping
2. `verify_and_fix_cloud_run.sh`: Script for verifying and troubleshooting the setup

## Important Notes
- Direct DNS resolution is required (no Cloudflare proxy)
- Cloud Run handles SSL/TLS termination
- All DNS records must use grey cloud (proxy off) in Cloudflare
- IAM policy allows unauthenticated access