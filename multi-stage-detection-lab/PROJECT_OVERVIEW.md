Multi-Stage Detection Lab

Endpoint Detection, Attack Simulation, and Response Engineering

What this project is

This lab is a hands-on security engineering environment built to practice realistic detection engineering, not just tool setup.

It simulates:

A small enterprise network

A monitored Windows endpoint

An attacker executing staged activity

Detection logic built from telemetry, not assumptions

The focus is how signals are created, collected, and turned into detections.

What problem this lab solves

Many entry-level security projects stop at:

“I installed an EDR”

“I ran an attack”

“I wrote a rule”

This lab goes further:

Telemetry is intentionally generated

Signals are validated

Detections are tied to specific attacker behavior

Each stage builds on the previous one

High-Level Architecture
[ Kali Linux Attacker ]
           |
           v
[ Ubuntu Gateway / SOAR Node ]
           |
           v
[ Windows Victim + Sysmon + LimaCharlie ]


Kali Linux simulates real attacker tradecraft

Ubuntu Gateway controls traffic and lab orchestration

Windows Victim generates endpoint telemetry

Sysmon + LimaCharlie provide high-fidelity signals

Repository Map (How to read this repo)
01-infrastructure/

How the lab is built

VM creation scripts

Network layout

Gateway setup

Endpoint configuration

Sysmon and EDR installation

If you want to reproduce the lab from scratch, start here.

02-detection-engineering/

How telemetry becomes detections

Detection logic

Event reasoning

Signal correlation

False-positive reduction

This is where raw data turns into security value.

03-attack-playbooks/

What the attacker actually does

Step-by-step attack scenarios

Realistic attacker behavior

Mapped to detection outcomes

Each playbook exists to force telemetry.

04-phishing-analysis-lab/

Email-based attack analysis

Phishing artifacts

Analysis workflow

Indicators and reasoning

Focused on thinking, not just tooling.

Skills demonstrated

Endpoint telemetry analysis

Detection engineering fundamentals

Linux system administration

Windows internals (processes, logs, persistence)

Network segmentation and control

Structured security documentation

Who this lab is for

This project is designed to demonstrate readiness for:

SOC Analyst I

Junior Detection Engineer

Entry-Level Security Engineer

Blue Team roles
