#!/bin/bash
influx -execute "CREATE USER admin WITH PASSWORD 'admin123' WITH ALL PRIVILEGES"
influx -execute "CREATE DATABASE ble_data"
