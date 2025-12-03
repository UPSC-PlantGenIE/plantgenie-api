# PlantGenIE FastAPI Backend

This is the REST API backend for PlantGenIE.

A local configuration is available that can be run via

```bash
docker compose --env-file <your-env-file>
```

## Graph/Network Notes

Spring Layout (`spring_layout`) is the Fruchterman-Reingold force-directed
algorithm that can be used for computing layouts via the Python library `networkx`.
