import subprocess

subprocess.run(["python3", "-m", "scripts.build_server_db"])
subprocess.run(["python3", "-m", "scripts.build_player_db"])

subprocess.run(["python3", "-m", "scripts.build_demon_db"])
subprocess.run(["python3", "-m", "scripts.build_races_db"])
subprocess.run(["python3", "-m", "scripts.build_fusion_db"])
subprocess.run(["python3", "-m", "scripts.build_fusion_chart_db"])
subprocess.run(["python3", "-m", "scripts.build_talk_db"])

subprocess.run(["python3", "-m", "scripts.build_items_db"])
subprocess.run(["python3", "-m", "scripts.build_badges_db"])

subprocess.run(["python3", "-m", "scripts.build_db_views"])
