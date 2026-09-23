"""Example course automation instances configuration template."""

from coursera_automation.instances import InstanceConfig

INSTANCES: list[InstanceConfig] = [
    InstanceConfig(
        email="your_email@example.com",
        password="your_password",
        course_url="https://www.coursera.org/specializations/your-course-url",
        headless=False,
        max_items=50,
    ),
    InstanceConfig(
        email="24bai71310@cuchd.in",
        password="Lhya24AI",
        course_url="https://www.coursera.org/organizations/chandigarh-university/specializations/generative-ai-for-software-developers",
        headless=False,
        max_items=50,
    ),
]
