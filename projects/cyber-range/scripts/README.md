# Scripts

Analysis and automation scripts for the cyber range.

## Files

| File | Purpose |
|------|---------|
| `analyze_rl.py` | Q-learning traffic analyzer using Ollama |
| `capture.sh` | Start tcpdump capture |
| `summarize.sh` | Generate tshark summary for LLM |
| `zeek-analyze.sh` | Run Zeek on PCAP and display logs |

## analyze_rl.py

AI-powered PCAP analyzer with Q-learning feedback loop.

```bash
# Activate venv
source ~/capture-env/bin/activate

# Analyze a capture
python3 scripts/analyze_rl.py capture.pcap

# View Q-table rankings
python3 scripts/analyze_rl.py --stats
```

### How Q-learning works

```
1. Detect attack type from traffic (state)
2. Choose best prompt+model from Q-table
3. Run Dolphin-Llama3 analysis
4. Rate output 1-5
5. Q-table updates
6. Next run automatically uses better combo
```

## Requirements

```bash
pip install ollama pyshark scapy zeek tshark
ollama pull dolphin-llama3:8b
```

> 🚧 Scripts coming soon
