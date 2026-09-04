#!/bin/bash
# Win Spares Quotation System - Public Sharing Script

echo "=========================================================="
echo " Starting Secure Public Tunnel for Win Spares Application "
echo "=========================================================="
echo "Ensure your app is running (e.g. via ./start.sh in another terminal)."
echo "Generating your live public link..."
echo ""

ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 nokey@localhost.run
