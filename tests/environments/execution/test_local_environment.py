import pytest

import prefect
from prefect.environments.execution import LocalEnvironment
from prefect.environments.storage import Memory
from prefect.environments.storage.docker import Docker


def test_create_environment():
    environment = LocalEnvironment()
    assert environment


def test_setup_environment_passes():
    environment = LocalEnvironment()
    environment.setup(storage=Docker())
    assert environment


def test_serialize_environment():
    environment = LocalEnvironment()
    env = environment.serialize()
    assert env["type"] == "LocalEnvironment"


def test_environment_execute():
    global_dict = {}

    @prefect.task
    def add_to_dict():
        global_dict["run"] = True

    environment = LocalEnvironment()
    storage = Memory()
    flow = prefect.Flow("test", tasks=[add_to_dict])
    flow_loc = storage.add_flow(flow)

    environment.execute(storage, flow_loc)
    assert global_dict.get("run") is True


def test_environment_execute_with_env_runner():
    class TestStorage(Memory):
        def get_flow(self, *args, **kwargs):
            raise NotImplementedError()

        def get_env_runner(self, flow_loc):
            runner = super().get_flow(flow_loc)
            return lambda env: runner.run()

    global_dict = {}

    @prefect.task
    def add_to_dict():
        global_dict["run"] = True

    environment = LocalEnvironment()
    storage = TestStorage()
    flow = prefect.Flow("test", tasks=[add_to_dict])
    flow_loc = storage.add_flow(flow)

    environment.execute(storage, flow_loc)
    assert global_dict.get("run") is True


def test_environment_execute_with_kwargs():
    global_dict = {}

    @prefect.task
    def add_to_dict(x):
        global_dict["result"] = x

    environment = LocalEnvironment()
    storage = Memory()
    with prefect.Flow("test") as flow:
        x = prefect.Parameter("x")
        add_to_dict(x)

    flow_loc = storage.add_flow(flow)

    environment.execute(storage, flow_loc, x=42)
    assert global_dict.get("result") == 42


def test_environment_execute_with_env_runner_with_kwargs():
    class TestStorage(Memory):
        def get_flow(self, *args, **kwargs):
            raise NotImplementedError()

        def get_env_runner(self, flow_loc):
            runner = super().get_flow(flow_loc)

            def runner_func(env):
                runner.run(x=env.get("x"))

            return runner_func

    global_dict = {}

    @prefect.task
    def add_to_dict(x):
        global_dict["result"] = x

    environment = LocalEnvironment()
    storage = TestStorage()
    with prefect.Flow("test") as flow:
        x = prefect.Parameter("x")
        add_to_dict(x)

    flow_loc = storage.add_flow(flow)
    environment.execute(storage, flow_loc, env=dict(x=42))
    assert global_dict.get("result") == 42
