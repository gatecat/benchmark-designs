#!/usr/bin/env python3
import os, sys, threading
from os import path
import subprocess
import re
from configparser import ConfigParser
from datetime import datetime

def main():
	num_runs = 16
	if len(sys.argv) == 1:
		benchmarks = [
			o for o in os.listdir(".") if path.isdir(o) and not o.startswith(".")
		]
	else:
		benchmarks = sys.argv[1:]
	for benchmark in benchmarks:
		print("Running {}...".format(benchmark))
		config = ConfigParser()
		config.read(path.join(benchmark, "config.ini"))
		runtime = []
		fmaxes = []
		threads = []
		if not path.exists(path.join(benchmark, ".work")):
			os.mkdir(path.join(benchmark, ".work"))
		for i in range(num_runs):
			def runner(run):
				logfile = path.join(".work", "s{}.log".format(run))
				if path.exists(path.join(benchmark, logfile)):
					os.remove(path.join(benchmark, logfile))
				try:
					start = datetime.now()
					args = ["nextpnr-{}".format(config['benchmark']['arch'])]
					args += config['benchmark']['args'].split(' ')
					args += ["-l", logfile, "--seed", str(run+1), "--timing-allow-fail"]
					output = subprocess.check_output(args, cwd=benchmark, stderr=subprocess.STDOUT)
					end = datetime.now()
					domain_fmaxes = re.findall(r'Max frequency for clock\s+\'([^\']+)\': ([0-9.]+) MHz', output.decode('utf-8'))
					clk_fmax = None
					target_domain = config['benchmark']['clk']
					for domain, fmax in domain_fmaxes:
						if domain == target_domain:
							clk_fmax = float(fmax)
					assert clk_fmax is not None, "clock domain {} not found!".format(target_domain)
					runtime.append((end - start).total_seconds())
					fmaxes.append(clk_fmax)
				except subprocess.CalledProcessError:
					print("    run {} failed!".format(run))
			threads.append(threading.Thread(target=runner, args=[i+1]))

		for t in threads: t.start()
		for t in threads: t.join()
		passed = len(fmaxes)
		print("{}/{} runs passed".format(passed, num_runs))
		if passed > 0:
			fmax_min = min(fmaxes)
			fmax_max = max(fmaxes)
			fmax_avg = sum(fmaxes) / len(fmaxes)
			runtime_min = min(runtime)
			runtime_max = max(runtime)
			runtime_avg = sum(runtime) / len(runtime)
			print("    Fmax: min = {:.2f} MHz, avg = {:.2f} MHz, max = {:.2f} MHz".format(fmax_min, fmax_avg, fmax_max))
			print("    Runtime: min = {:.2f}s, avg = {:.2f}s, max = {:.2f}s".format(runtime_min, runtime_avg, runtime_max))

if __name__ == '__main__':
	main()
