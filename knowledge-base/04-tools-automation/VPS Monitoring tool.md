## Key Features
1. **Real-time Monitoring**: CPU, RAM, disk, network via Node Exporter + cAdvisor
2. **Container Metrics**: Per-container resource usage with cAdvisor
3. **Hostinger API Integration**: Custom exporter fetching metrics from Hostinger API
4. **Control API**: FastAPI service with start/stop/restart endpoints
5. **3 Pre-configured Dashboards**: VPS Overview, Docker & Services, Hostinger Control
6. **Security**: All services localhost-bound, ready for Cloudflare Tunnel exposure

# File structure
```
monitoring/
├── docker-compose.monitoring.yml    # Main compose file for all services
├── .env                             # Environment variables (with your API token)
├── .env.example                     # Template for environment variables
├── .gitignore                       # Excludes sensitive files
├── README.md                        # Complete documentation
├── prometheus/
│   └── prometheus.yml               # Prometheus scrape configuration
├── grafana/
│   ├── grafana.ini                  # Grafana configuration
│   └── provisioning/
│       ├── datasources/datasources.yml
│       └── dashboards/
│           ├── dashboards.yml
│           └── json/
│               ├── vps-overview.json      # System metrics dashboard
│               ├── docker-services.json   # Container metrics dashboard
│               └── hostinger-control.json # Hostinger API dashboard
├── hostinger-exporter/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── exporter.py                  # Custom Prometheus exporter for Hostinger API
└── control-api/
    ├── Dockerfile
    ├── requirements.txt
    └── main.py                      # FastAPI REST API for VPS control
```
## To Deploy
```
cd monitoring
docker compose -f docker-compose.monitoring.yml up -d
```

Then access:

- **Grafana**: [http://localhost:3000](http://localhost:3000/) (admin / VpsM0n1t0r!ng2024)
- **Prometheus**: [http://localhost:9090](http://localhost:9090/)
- **Control API**: [http://localhost:9102/docs](http://localhost:9102/docs)

Would you like me to test the setup or make any adjustments?