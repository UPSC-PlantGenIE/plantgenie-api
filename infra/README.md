# PlantGenIE OpenStack Deployment

The IaaC (terraform) deployments (dev and prod) for the PlantGenIE web application.

# Final Steps

1. Update A records on domain provider for plantgenie.upsc.se, www.plantgenie.se (prod) and dev.plantgenie.se (dev)

2. Install certbot on the nginx VMs. This should already be done via
cloud-init, but just in case:

```bash
sudo apt install certbot python3-certbot-nginx
```

3. Run it!

```bash
sudo certbot --nginx \
    -d dev.plantgenie.se \
    -m jamie.mccann@umu.se \
    -n \
    --agree-tos
```

or

```bash
sudo certbot --nginx \
    -d plantgenie.se,www.plantgenie.se,plantgenie.upsc.se \
    -m jamie.mccann@umu.se \
    -n \
    --agree-tos

```

# Useful Commands for Deployment

- plan terraform deployment
```bash
terraform plan --var-file north-{prod,dev}.tfvars
```

- apply terraform deployment
```bash
terraform apply --var-file north-{prod,dev}.tfvars
```

- monitor cloud-init (after ssh-ing into the deployed VM)
```bash
sudo tail -f /var/log/cloud-init-output.log
```
