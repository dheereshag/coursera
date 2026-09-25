"""Example course automation instances configuration template."""

from coursera_automation.instances import InstanceConfig

INSTANCES: list[InstanceConfig] = [
    # for first course
    InstanceConfig(
        email="24bai71310@cuchd.in",
        password="Lhya24AI",
        course_url="https://www.coursera.org/organizations/chandigarh-university/specializations/generative-ai-for-software-developers",
        legal_name="Your Legal Name",
        headless=False,
        max_items=50,
    ),
    # for second course
    InstanceConfig(
        email="24bai71310@cuchd.in",
        password="Lhya24AI",
        course_url="https://www.coursera.org/organizations/chandigarh-university/specializations/generative-ai-for-software-developers",
        legal_name="Your Legal Name",
        headless=False,
        max_items=50,
    ),
]
