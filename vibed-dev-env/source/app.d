module app;

import vibe.vibe;
import std.process : environment;

void main()
{
    auto settings = new HTTPServerSettings;
    settings.port = 8080;
    settings.bindAddresses = ["0.0.0.0"];

    auto router = new URLRouter;

    // Health check endpoint
    router.get("/health", (scope req, scope res) {
        res.writeJsonBody(["status": "healthy", "service": "vibed-app"]);
    });

    // Root endpoint
    router.get("/", (scope req, scope res) {
        res.writeBody("Welcome to Vibe.d!");
    });

    // API endpoints
    router.get("/api/info", (scope req, scope res) {
        res.writeJsonBody([
            "name": "vibed-app",
            "version": "0.1.0",
            "environment": environment.get("ENVIRONMENT", "development")
        ]);
    });

    auto listener = listenHTTP(settings, router);
    scope(exit) listener.stopListening();

    logInfo("Vibe.d server running on http://0.0.0.0:8080");
    runApplication();
}
