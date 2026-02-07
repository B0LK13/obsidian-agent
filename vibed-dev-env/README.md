# Vibe.d Development Environment

Advanced, containerized development environment for Vibe.d on Windows 11 Pro with WSL2, Docker, GitPod, and GitHub Actions.

## Prerequisites

### Windows 11 Pro Host

1. **Enable WSL2 and Virtual Machine Platform** (PowerShell as Administrator):
   ```powershell
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
   ```

2. **Set WSL2 as default**:
   ```powershell
   wsl --set-default-version 2
   ```

3. **Install Ubuntu 22.04 LTS** from Microsoft Store

4. **Install Docker Desktop for Windows**
   - Enable WSL2 backend in Docker Desktop settings
   - Enable your Ubuntu distribution in Docker Desktop → Resources → WSL Integration

### VS Code Extensions

Install the following extensions:
- **Remote - Containers** (`ms-vscode-remote.remote-containers`)
- **CodeLLDB** (`vadimcn.vscode-lldb`)
- **D Language** (`webfreak.code-d`)
- **Docker** (`ms-azuretools.vscode-docker`)
- **GitLens** (`eamodio.gitlens`)

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd vibed-dev-env

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

### Option 2: VS Code Dev Containers

1. Open the project in VS Code
2. Press `F1` → "Dev Containers: Reopen in Container"
3. Wait for the container to build and start
4. Start coding!

### Option 3: GitPod

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#<your-repo-url>)

## Project Structure

```
vibed-dev-env/
├── .devcontainer/          # VS Code Dev Container configuration
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── vibed-ci.yml    # GitHub Actions CI/CD pipeline
├── .gitpod.yml             # GitPod configuration
├── .gitpod.Dockerfile      # GitPod container image
├── .vscode/
│   ├── launch.json         # Debug configurations
│   └── tasks.json          # Build tasks
├── docker/
│   ├── init-db/            # Database initialization scripts
│   └── nginx/              # Nginx configuration
├── source/
│   └── app.d               # Main application source
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Service orchestration
├── dub.json                # D package configuration
└── README.md
```

## Development Workflow

### Building

```bash
# Debug build (DMD)
dub build --compiler=dmd --build=debug

# Release build (LDC - optimized)
dub build --compiler=ldc2 --build=release
```

### Running

```bash
# Run with DMD
dub run --compiler=dmd

# Run with Docker Compose
docker-compose up app
```

### Testing

```bash
# Run unit tests
dub test --compiler=dmd

# Run integration tests (requires services)
docker-compose up -d db redis
dub test --compiler=dmd -- --integration
```

### Debugging

1. Set breakpoints in VS Code
2. Press `F5` or select "Debug Vibe.d App (DMD)" from the debug panel
3. The debugger will attach using CodeLLDB

## Services

| Service | Port | Description |
|---------|------|-------------|
| Vibe.d App | 8080 | Main application |
| Debug/Metrics | 9090 | Debug and metrics endpoint |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache |
| Adminer | 8082 | Database UI (tools profile) |
| Redis Commander | 8083 | Redis UI (tools profile) |

### Starting Additional Tools

```bash
# Start with database management tools
docker-compose --profile tools up -d

# Start with production-like nginx proxy
docker-compose --profile production up -d
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/vibed-ci.yml`) provides:

- **Build Matrix**: Tests with DMD and LDC on multiple Ubuntu versions
- **Code Quality**: D-Scanner static analysis and dfmt formatting checks
- **Security Scanning**: Trivy vulnerability scanning
- **Docker Build**: Automated container image builds
- **Integration Tests**: Full stack testing with PostgreSQL and Redis
- **Release Automation**: Automatic releases on version tags

### Triggering Builds

- **Push to `main` or `develop`**: Full CI pipeline
- **Pull Requests**: Build, test, and code quality checks
- **Version Tags (`v*`)**: Full pipeline + release creation

## Compiler Options

| Compiler | Use Case | Build Command |
|----------|----------|---------------|
| DMD | Fast compilation, debugging | `dub build --compiler=dmd` |
| LDC | Optimized release builds | `dub build --compiler=ldc2 --build=release` |

### Release Build Flags

```bash
# Maximum optimization with LDC
dub build --compiler=ldc2 --build=release
# Equivalent to: -O3 -release -inline -boundscheck=off
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Runtime environment |
| `LOG_LEVEL` | `debug` | Logging verbosity |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://...` | Redis connection string |
| `DUB_COMPILER` | `dmd` | Default D compiler |

## Troubleshooting

### Docker Issues

```bash
# Rebuild containers from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### WSL2 Issues

```powershell
# Restart WSL
wsl --shutdown
wsl

# Check WSL version
wsl --list --verbose
```

### D Compiler Issues

```bash
# Verify compiler installation
dmd --version
ldc2 --version
dub --version

# Clear DUB cache
rm -rf ~/.dub
dub fetch
```

## Performance Profiling

```bash
# Build with profiling
dub build --compiler=ldc2 --build=profile

# Run with perf (Linux)
perf record -g ./app
perf report

# Memory profiling with Valgrind
valgrind --tool=massif ./app
```

## Security Best Practices

1. **Secrets Management**: Never commit `.env` files; use `.env.example` as template
2. **Container Security**: Images run as non-root user `ddev`
3. **Dependency Scanning**: Trivy scans in CI pipeline
4. **Network Isolation**: Services communicate via Docker network

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
