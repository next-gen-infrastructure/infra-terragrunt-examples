import os
import setuptools

name = "infra-terragrunt-examples"
description = "Generate example terragrunt.hcl files for the terraform modules from the variable descriptions"
version = {}
package_root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(package_root, "nextgeninfrastructure/version.py")) as fp:
    exec(fp.read(), version)
version = version["__version__"]
# Should be one of:
# 'Development Status :: 3 - Alpha'
# 'Development Status :: 4 - Beta'
# 'Development Status :: 5 - Production/Stable'
release_status = "Development Status :: 4 - Beta"
dependencies = ["jinja2", "GitPython"]
entry_points = {
    "console_scripts": ["generate-examples=nextgeninfrastructure.generate:main"],
}

package_root = os.path.abspath(os.path.dirname(__file__))
packages = setuptools.find_namespace_packages()

setuptools.setup(
    name=name,
    version=version,
    description=description,
    author="NextGen Infrastructure",
    author_email="8377544+ADobrodey@users.noreply.github.com",
    license="MIT License",
    url="https://github.com/next-gen-infrastructure/infra-terragrunt-examples",
    entry_points=entry_points,
    classifiers=[
        release_status,
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Internet",
    ],
    platforms="Posix; MacOS X; Windows",
    packages=packages,
    install_requires=dependencies,
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
)
