# OpenList-fnOS

将 [OpenListTeam/OpenList](https://github.com/OpenListTeam/OpenList) 的官方 Linux amd64 Release 自动封装为 **fnOS x86 原生 FPK**。

- 不使用 Docker
- 默认端口：5244
- GitHub Actions 每 24 小时检查一次上游最新正式 Release
- 发现新版本后自动生成 FPK，并创建 GitHub Pre-release
- 支持 Actions 页面手动指定版本构建
- 使用已经验证过的 `openlistnative` FPK 骨架

## 仓库结构

```text
.github/workflows/build-openlist-fpk.yml
package-template/
scripts/build_fpk.sh
README.md
.gitignore
```

## 自动检测

每天一次，约北京时间 09:17。

## 上游版本与旧包迁移

新 FPK 的 manifest、文件名和 Release tag 直接使用上游版本 `4.2.6`，不再添加封装修订号。同一个上游版本只发布一次，不能静默替换同版本 FPK。

FnDepot 先前索引的版本为 `4.2.6-native1`。已安装的旧包可能因版本号比较或安装来源无法自动升级；切换版本规则需要在设备上单独验证和迁移。
