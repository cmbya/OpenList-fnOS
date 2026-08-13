# OpenList-fnOS

将 [OpenListTeam/OpenList](https://github.com/OpenListTeam/OpenList) 的官方 Linux amd64 Release 自动封装为 **fnOS x86 原生 FPK**。

- 不使用 Docker
- 默认端口：5244
- 当前 fnOS 封装版本：见 `PACK_REV`
- GitHub Actions 每 24 小时检查一次上游最新正式 Release
- 发现新版本后自动生成 FPK，并创建 GitHub Pre-release
- 支持 Actions 页面手动指定版本构建
- 使用已经验证过的 `openlistnative` FPK 骨架

## 仓库结构

```text
.github/workflows/build-openlist-fpk.yml
package-template/
scripts/build_fpk.sh
PACK_REV
README.md
.gitignore
```

`.build/` 和 `dist/` 是构建时临时目录，不要上传；已经写进 `.gitignore`。

## 第一次使用

1. 新建公开仓库 `OpenList-fnOS`。
2. 上传本仓库模板文件。
3. 如果网页上传隐藏 `.github`，在 GitHub 使用 **Add file → Create new file**，文件名输入：
   `.github/workflows/build-openlist-fpk.yml`
4. Settings → Actions → General → Workflow permissions → 选择 **Read and write permissions** → Save。
5. Actions → **Build OpenList fnOS FPK** → Run workflow。
6. `version` 留空会自动使用上游最新正式 Release。

## 自动检测

定时任务：

```yaml
- cron: "17 1 * * *"
```

即每天一次，约北京时间 09:17。

## 版本说明

例如：

```text
OpenList_4.2.5_native1_fnOS_x86.fpk
```

其中 `4.2.5` 是 OpenList 上游版本，`native1` 是 fnOS 封装版本。

如果以后只修改飞牛封装而上游版本没变，把 `PACK_REV` 从 `native1` 改为 `native2`，再手动 Run workflow 即可生成新的 FPK。
