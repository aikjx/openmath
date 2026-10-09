#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""openmath 单库一键发版脚本（提交 -> 打备份标签 -> 推送）。

用法（在 openmath 仓库根目录或任意位置执行）：
  python scripts/git_release.py                # 提交 + 打备份 tag + 推送（默认）
  python scripts/git_release.py --dry-run      # 只打印将要执行的操作
  python scripts/git_release.py --no-push      # 只提交 + 打 tag，不推送
  python scripts/git_release.py --push-only    # 只推送已有提交与标签
  python scripts/git_release.py --tag-prefix tag   # 换标签前缀（默认 backup）
  python scripts/git_release.py --remote origin    # 只推指定远端（可重复）
  python scripts/git_release.py --git-exe "C:/.../git.exe"

设计要点：
  1. 仓库根 = 本脚本所在目录的上一级（openmath/scripts/ -> openmath/）。
  2. 标签命名 backup-<分支>-YYYYMMDD_HHMMSS，已存在则跳过，绝不覆盖。
  3. 双远端（origin=github, gitcode=gitcode）逐个推送，单个远端失败不影响其它。
  4. 安全：令牌只经 credential.helper=store 从 ~/.git-credentials 读取，
     不进 argv / URL / 日志；所有回显与异常日志经 mask() 脱敏。
"""
import os
import re
import sys
import argparse
import datetime
import subprocess

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def mask(text):
    """统一脱敏：URL 内嵌凭据 / GitHub 令牌 / Authorization 头。"""
    if text is None:
        return text
    s = str(text)
    s = re.sub(r"(://[^:]+:)[^@]+(@)", r"\1****\2", s)
    s = re.sub(r"gh[oprsu]_[A-Za-z0-9]{20,}", "gho_****", s)
    s = re.sub(r"github_pat_[A-Za-z0-9_]{20,}", "****", s)
    s = re.sub(r"(?i)(authorization:\s*)[^\r\n]+", r"\1****", s)
    return s


def git_env(git_exe):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    if git_exe and "PortableGit" in git_exe:
        bin_dir = os.path.dirname(git_exe)
        usr_bin = os.path.join(os.path.dirname(bin_dir), "usr", "bin")
        env["PATH"] = bin_dir + os.pathsep + usr_bin + os.pathsep + env.get("PATH", "")
    return env


def run(git_exe, repo, args, dry_run=False, timeout=600):
    disp = " ".join(mask(a) for a in args)
    print("\n$ git " + disp + "   (cwd=" + repo + ")", flush=True)
    if dry_run:
        return None
    try:
        r = subprocess.run([git_exe, *args], cwd=repo, env=git_env(git_exe),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        print("  !! 超时 " + str(timeout) + "s（疑似网络/代理阻断）：git " + disp, flush=True)
        return None
    except Exception as e:
        print("  !! 执行异常 " + type(e).__name__ + "：git " + disp, flush=True)
        return None
    print("  rc =", r.returncode, flush=True)
    if r.stdout and r.stdout.strip():
        print("  STDOUT:\n" + mask(r.stdout.rstrip()), flush=True)
    if r.stderr and r.stderr.strip():
        print("  STDERR:\n" + mask(r.stderr.rstrip()[-3000:]), flush=True)
    return r


def out(git_exe, repo, args):
    r = subprocess.run([git_exe, *args], cwd=repo, env=git_env(git_exe),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    return r.stdout.strip() if r.returncode == 0 else ""


def is_dirty(git_exe, repo):
    s = out(git_exe, repo, ["-c", "core.quotePath=false", "status", "--porcelain"])
    return bool(s)


def branch_of(git_exe, repo):
    return out(git_exe, repo, ["rev-parse", "--abbrev-ref", "HEAD"]) or "main"


def remotes(git_exe, repo, only):
    """返回 [(远端名, pushurl)]；only 非空时按名字过滤。"""
    seen, res = set(), []
    for line in out(git_exe, repo, ["remote", "-v"]).splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[-1] == "(push)":
            name, url = parts[0], parts[1]
            if only and name not in only:
                continue
            if url in seen:
                continue
            seen.add(url)
            res.append((name, url))
    return res


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="openmath 单库提交/打备份标签/推送")
    ap.add_argument("--repo", default=os.path.dirname(here), help="仓库根目录")
    ap.add_argument("--git-exe", default="git")
    ap.add_argument("--message", default=None, help="提交信息")
    ap.add_argument("--tag-prefix", default="backup", help="标签前缀，默认 backup")
    ap.add_argument("--remote", action="append", default=[], help="只推该远端名（可重复）")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--push-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    git_exe = args.git_exe
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    branch = branch_of(git_exe, repo)
    tag = args.tag_prefix + "-" + branch + "-" + ts
    msg = args.message or ("chore(release): auto " + ts)

    print("[openmath] repo = " + repo, flush=True)
    print("[openmath] branch = " + branch + " ; tag = " + tag, flush=True)

    if not args.push_only:
        if is_dirty(git_exe, repo):
            run(git_exe, repo, ["add", "-A"], dry_run=args.dry_run)
            r = run(git_exe, repo, ["commit", "-m", msg], dry_run=args.dry_run)
            if r is not None and r.returncode != 0:
                print("  !! 提交失败，终止（不推送）", flush=True)
                return 1
        else:
            print("  工作树干净，无需提交", flush=True)

    r = run(git_exe, repo, ["rev-parse", "-q", "--verify", "refs/tags/" + tag],
            dry_run=args.dry_run)
    if r is not None and r.returncode == 0:
        print("  标签 " + tag + " 已存在，跳过", flush=True)
    else:
        run(git_exe, repo, ["tag", "-a", tag, "-m", "Backup tag " + ts], dry_run=args.dry_run)

    if args.no_push:
        print("  --no-push：跳过推送", flush=True)
        return 0

    cred_opts = ["-c", "credential.helper=", "-c", "credential.helper=store"]
    ok = True
    for name, url in remotes(git_exe, repo, args.remote):
        print("\n---- 远端 " + name + " -> " + mask(url) + " ----", flush=True)
        r1 = run(git_exe, repo, [*cred_opts, "push", name, branch], dry_run=args.dry_run)
        r2 = run(git_exe, repo, [*cred_opts, "push", name, tag], dry_run=args.dry_run)
        if (r1 is not None and r1.returncode != 0) or (r2 is not None and r2.returncode != 0):
            ok = False
    print("\n==== openmath 完成（ok=" + str(ok) + "）====", flush=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
