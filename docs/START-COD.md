# Start Cod

Run these from the project folder (the saved mode from the Models page is used when no flag is given).

- `cod.cmd` - starts with the saved mode (default auto: your Claude plan, free models in the same session at the limit).
- `cod.cmd --free` - free models only through the router; your plan is never used.
- `cod.cmd --plan` - your Claude plan only, without the router.
- `cod.cmd --safe` - work goes to free models through the router while the plan login is kept (no placeholder token); only the safety check uses the plan.

Other arguments are passed on to claude.
