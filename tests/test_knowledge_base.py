#!/usr/bin/env python3
"""
知识库测试 - 验证 Skill 集成功能
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.knowledge_base import KnowledgeBase

class TestKnowledgeBase(unittest.TestCase):
    def test_docs_loaded(self):
        kb = KnowledgeBase('docs')
        self.assertEqual(len(kb.doc_cache), 7)
        print(f"✅ 加载 {len(kb.doc_cache)} 个参考文档")
    
    def test_bottleneck_rules(self):
        kb = KnowledgeBase('docs')
        self.assertEqual(len(kb.BOTTLENECK_RULES), 4)
        print(f"✅ {len(kb.BOTTLENECK_RULES)} 类瓶颈规则")
    
    def test_optimization_templates(self):
        kb = KnowledgeBase('docs')
        self.assertEqual(len(kb.OPTIMIZATION_TEMPLATES), 5)
        print(f"✅ {len(kb.OPTIMIZATION_TEMPLATES)} 个优化模板")

if __name__ == '__main__':
    unittest.main(verbosity=2)
