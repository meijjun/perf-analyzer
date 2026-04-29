#!/usr/bin/env python3
"""
打包服务 - 自动压缩项目并提供下载
"""

import os
import json
import logging
import shutil
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class PackageService:
    """项目打包服务"""
    
    def __init__(self, project_root: str = "../"):
        self.project_root = Path(project_root)
        self.build_dir = self.project_root / "build"
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.version_file = self.project_root / "VERSION.json"
    
    def get_version(self) -> str:
        """获取当前版本号"""
        if not self.version_file.exists():
            return "1.0.0"
        
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            return version_data.get('version', '1.0.0')
        except:
            return "1.0.0"
    
    def update_version(self, version: str) -> bool:
        """更新版本号"""
        try:
            version_data = {}
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
            
            version_data['version'] = version
            version_data['build_date'] = datetime.now().strftime('%Y-%m-%d')
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 版本号已更新：{version}")
            return True
        except Exception as e:
            logger.error(f"更新版本号失败：{e}")
            return False
    
    def create_package(self, format: str = 'zip', 
                      include_data: bool = False,
                      include_logs: bool = False) -> Tuple[bool, str]:
        """创建项目包
        
        Args:
            format: 压缩格式 (zip/tar.gz)
            include_data: 是否包含 data 目录
            include_logs: 是否包含 logs 目录
        
        Returns:
            (success, package_path)
        """
        try:
            version = self.get_version()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            package_name = f"perf-analyzer-v{version}_{timestamp}"
            
            # 清理旧的构建文件
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
            self.build_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建临时目录
            temp_dir = self.build_dir / package_name
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制项目文件
            self._copy_project_files(temp_dir, include_data, include_logs)
            
            # 创建 VERSION.txt
            self._create_version_txt(temp_dir)
            
            # 创建 README
            self._create_readme(temp_dir)
            
            # 压缩
            if format == 'zip':
                package_path = self._create_zip(package_name)
            else:
                package_path = self._create_tar_gz(package_name)
            
            logger.info(f"✅ 项目包已创建：{package_path}")
            return True, str(package_path)
            
        except Exception as e:
            logger.error(f"创建项目包失败：{e}")
            import traceback
            traceback.print_exc()
            return False, str(e)
    
    def _copy_project_files(self, dest_dir: Path, include_data: bool, include_logs: bool):
        """复制项目文件"""
        # 需要复制的目录
        dirs_to_copy = [
            'backend',
            'frontend',
            'config'
        ]
        
        # 需要复制的文件
        files_to_copy = [
            'VERSION.json',
            'requirements.txt' if (self.project_root / 'requirements.txt').exists() else None
        ]
        
        # 复制目录
        for dir_name in dirs_to_copy:
            src = self.project_root / dir_name
            if src.exists():
                dest = dest_dir / dir_name
                shutil.copytree(src, dest, 
                              ignore=self._ignore_patterns(dir_name, include_data, include_logs))
                logger.info(f"  复制目录：{dir_name}")
        
        # 复制文件
        for file_name in files_to_copy:
            if file_name:
                src = self.project_root / file_name
                if src.exists():
                    shutil.copy2(src, dest_dir / file_name)
                    logger.info(f"  复制文件：{file_name}")
    
    def _ignore_patterns(self, dir_name: str, include_data: bool, include_logs: bool):
        """忽略模式"""
        def ignore_func(path, names):
            ignored = []
            for name in names:
                # 忽略 Python 缓存
                if name in ['__pycache__', '*.pyc', '*.pyo']:
                    ignored.append(name)
                # 忽略虚拟环境
                if name in ['venv', 'env', '.venv']:
                    ignored.append(name)
                # 忽略 data 目录（除非明确包含）
                if dir_name == '' and name == 'data' and not include_data:
                    ignored.append(name)
                # 忽略 logs 目录（除非明确包含）
                if dir_name == '' and name == 'logs' and not include_logs:
                    ignored.append(name)
                # 忽略 build 目录
                if dir_name == '' and name == 'build':
                    ignored.append(name)
            return ignored
        return ignore_func
    
    def _create_version_txt(self, dest_dir: Path):
        """创建版本说明文件"""
        version = self.get_version()
        build_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        version_content = f"""性能分析器 - 版本信息
========================

版本号：{version}
构建时间：{build_date}

项目地址：https://github.com/meijjun/perf-analyzer

快速开始:
1. 安装依赖：pip install -r requirements.txt
2. 启动服务：cd backend && python3 app.py
3. 访问页面：http://localhost:5000/

详细文档请参考项目 README.md
"""
        
        with open(dest_dir / 'VERSION.txt', 'w', encoding='utf-8') as f:
            f.write(version_content)
    
    def _create_readme(self, dest_dir: Path):
        """创建快速入门 README"""
        version = self.get_version()
        
        readme_content = f"""# 性能分析器 v{version}

## 快速开始

### 1. 环境要求
- Python 3.8+
- Linux/Unix 系统（推荐）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置
编辑 `config/config.yaml` 配置大模型 API Key

### 4. 启动服务
```bash
cd backend
python3 app.py
```

### 5. 访问
打开浏览器访问：http://localhost:5000/

## 主要功能

- 🔍 SSH/Telnet 远程性能分析
- 📊 持续监控模式
- 📝 采集命令管理
- 📈 数据可视化
- ⚠️ 告警系统
- 📄 报告导出（PDF/Excel）

## 文档

详细文档请访问：https://github.com/meijjun/perf-analyzer

---
构建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(dest_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _create_zip(self, package_name: str) -> Path:
        """创建 ZIP 压缩包"""
        package_path = self.build_dir / f"{package_name}.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.build_dir / package_name):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arcname)
                    logger.debug(f"  添加：{arcname}")
        
        return package_path
    
    def _create_tar_gz(self, package_name: str) -> Path:
        """创建 TAR.GZ 压缩包"""
        package_path = self.build_dir / f"{package_name}.tar.gz"
        
        with tarfile.open(package_path, "w:gz") as tar:
            tar.add(self.build_dir / package_name, 
                   arcname=package_name)
        
        return package_path
    
    def get_package_info(self, package_path: str) -> dict:
        """获取包信息"""
        path = Path(package_path)
        if not path.exists():
            return {'exists': False}
        
        stat = path.stat()
        return {
            'exists': True,
            'filename': path.name,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }


# 全局单例
_package_service = None

def get_package_service() -> PackageService:
    """获取打包服务单例"""
    global _package_service
    if _package_service is None:
        _package_service = PackageService()
    return _package_service
