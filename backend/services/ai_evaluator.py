"""
AI 评价服务模块
使用大语言模型对今日的 Git 活动进行可爱鼓励的评价
"""

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AIEvaluator:
    """AI 评价器"""

    def __init__(self, config: Dict):
        """
        初始化 AI 评价器

        Args:
            config: AI 配置字典
        """
        self.enabled = config.get('enabled', False)
        self.api_key = config.get('api_key', '')
        self.api_url = config.get('api_url', 'https://api.openai.com/v1/chat/completions')
        self.model = config.get('model', 'gpt-4o-mini')
        self.max_tokens = config.get('max_tokens', 500)
        self.temperature = config.get('temperature', 0.8)

        # 检查是否启用
        if not self.enabled or not self.api_key:
            logger.info("AI 评价功能未启用或未配置 API Key")
            self.enabled = False

    def _create_prompt(self, today_stats: Dict, activities: List[Dict]) -> str:
        """
        创建 AI 提示词

        Args:
            today_stats: 今日统计信息
            activities: 今日活动列表

        Returns:
            提示词字符串
        """
        commit_count = today_stats.get('commit_count', 0)
        push_count = today_stats.get('push_count', 0)

        # 提取最近的活动信息
        recent_activities = activities[:10]  # 只取最近10条
        activity_summaries = []
        for activity in recent_activities:
            repo_name = activity.get('repo_name', '未知仓库')
            commit_msg = activity.get('commit_message', '无消息')[:50]
            activity_type = '提交' if activity.get('activity_type') == 'commit' else '推送'
            activity_summaries.append(f"- {activity_type}: {repo_name} - {commit_msg}")

        activities_text = '\n'.join(activity_summaries) if activity_summaries else '暂无活动记录'

        prompt = f"""你是一个可爱、温暖、充满鼓励、比较幽默的二次元萌妹助手~ 💖

请以可爱甜美、充满正能量的语气,对用户今天的 Git 开发活动进行评价和鼓励。

## 今日活动统计
- 提交次数: {commit_count} 次 💝
- 推送次数: {push_count} 次 ✈️

## 最近活动
{activities_text}

## 评价要求
1. **语气风格**:
   - 使用可爱、温暖、充满鼓励的语气
   - 语气更加有活人感觉,避免过于机械化
   - 适当使用 emoji 表情符号 (💖✨🌟💪等)
   - 可以用"主人"称呼用户,或者用"你"都可以
   - 整体要给人温暖、被鼓励的感觉

2. **评价内容**:
   - 根据提交和推送数量给予肯定和赞赏
   - 如果工作量较大,要提醒用户注意休息
   - 如果工作量较小,要温和鼓励继续努力
   - 可以适当提及具体的项目或提交内容
   - 要真诚、温暖、不夸张

3. **字数要求**: 50-150字左右,不要太长

请给出你的评价:"""

        return prompt

    def evaluate_today(self, today_stats: Dict, activities: List[Dict]) -> Optional[str]:
        """
        评价今日活动

        Args:
            today_stats: 今日统计信息
            activities: 今日活动列表

        Returns:
            AI 评价文本,如果失败则返回 None
        """
        if not self.enabled:
            return None

        try:
            # 创建提示词
            prompt = self._create_prompt(today_stats, activities)

            # 调用 API
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是一个可爱、温暖、充满鼓励的二次元萌妹助手,名字叫"萌妹酱"。你善于用温暖的语言鼓励和赞赏他人。'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': self.max_tokens,
                'temperature': self.temperature
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            result = response.json()

            # 提取评价文本
            evaluation = result['choices'][0]['message']['content'].strip()
            logger.info(f"AI 评价生成成功: {evaluation[:50]}...")
            return evaluation

        except requests.exceptions.Timeout:
            logger.error("AI API 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"AI API 请求失败: {str(e)}")
            # 记录响应内容以便调试
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"响应状态码: {e.response.status_code}")
                logger.error(f"响应内容: {e.response.text[:500]}")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"AI API 响应解析失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"AI 评价生成失败: {str(e)}")
            return None

    def get_fallback_evaluation(self, today_stats: Dict) -> str:
        """
        获取默认评价(当 AI 不可用时)

        Args:
            today_stats: 今日统计信息

        Returns:
            默认评价文本
        """
        commit_count = today_stats.get('commit_count', 0)
        push_count = today_stats.get('push_count', 0)

        if commit_count == 0 and push_count == 0:
            return "今天还没有提交记录哦~ 💖 无论多忙,也要记得给自己留点时间呢!明天继续加油吧! ✨"

        total = commit_count + push_count

        if total >= 10:
            return f"哇!主人今天超级努力呢! 💪 完成了 {commit_count} 次提交和 {push_count} 次推送,太厉害了! 🌟 但是也要注意休息哦,身体最重要~ 💖"

        elif total >= 5:
            return f"今天也很棒呢! ✨ 完成了 {commit_count} 次提交和 {push_count} 次推送,继续保持这个节奏! 💪 每一点进步都值得被看见~ 💖"

        else:
            return f"今天也有在努力哦! 💝 完成了 {commit_count} 次提交和 {push_count} 次推送,积少成多,坚持下去会更好! ✨ 萌妹酱为你加油! 🌟"
