from deep_rl import *


def batch_mujoco():
    cf = Config()
    cf.add_argument('--i', type=int, default=0)
    cf.add_argument('--j', type=int, default=0)
    cf.merge()

    games = [
        'dm-acrobot-swingup',
        'dm-acrobot-swingup_sparse',
        'dm-ball_in_cup-catch',
        'dm-cartpole-swingup',
        'dm-cartpole-swingup_sparse',
        'dm-cartpole-balance',
        'dm-cartpole-balance_sparse',
        'dm-cheetah-run',
        'dm-finger-turn_hard',
        'dm-finger-spin',
        'dm-finger-turn_easy',
        'dm-fish-upright',
        'dm-fish-swim',
        'dm-hopper-stand',
        'dm-hopper-hop',
        'dm-humanoid-stand',
        'dm-humanoid-walk',
        'dm-humanoid-run',
        'dm-manipulator-bring_ball',
        'dm-pendulum-swingup',
        'dm-point_mass-easy',
        'dm-reacher-easy',
        'dm-reacher-hard',
        'dm-swimmer-swimmer15',
        'dm-swimmer-swimmer6',
        'dm-walker-stand',
        'dm-walker-walk',
        'dm-walker-run',
    ]

    # games = ['HalfCheetah-v2', 'Walker2d-v2', 'Swimmer-v2', 'Hopper-v2', 'Reacher-v2']
    games = ['HalfCheetah-v2', 'Walker2d-v2', 'Swimmer-v2', 'Hopper-v2']
    # games = ['dm-walker', 'dm-cartpole-b', 'dm-reacher', 'dm-fish', 'dm-cheetah']

    params = []

    # for game in games:
    #     for r in range(2):
    #         for num_o in [4]:
    #             for learning in ['all']:
    #                 for opt_ep in [5, 10]:
    #                     for entropy_weight in [0, 0.01]:
    #                         params.append([a_squared_c_ppo_continuous,
    #                                        dict(game=game, run=r, learning=learning, num_o=num_o, opt_ep=opt_ep,
    #                                             entropy_weight=entropy_weight, tasks=False)])
    #         params.append([ppo_continuous, dict(game=game, run=r, tasks=False)])

    for game in games:
        for r in range(10):
            # params.append([a_squared_c_ppo_continuous, dict(game=game, run=r, tasks=True, remark='ASC')])
            # params.append([ppo_continuous, dict(game=game, run=r, tasks=True, remark='PPO')])
            # params.append([ahp_ppo_continuous, dict(game=game, run=r, tasks=True, remark='AHP')])

            # params.append([a_squared_c_ppo_continuous, dict(game=game, run=r, tasks=False, remark='ASC', gate=nn.Tanh())])
            # params.append([a_squared_c_a2c_continuous, dict(game=game, run=r, tasks=False, remark='A2C', gate=nn.Tanh())])
            # params.append([ahp_ppo_continuous, dict(game=game, run=r, tasks=False, remark='AHP', gate=nn.Tanh())])
            params.append([iopg_continuous, dict(game=game, run=r, tasks=False, remark='IOPG', gate=nn.Tanh())])

    # params = []
    # for r in range(2):
    #     for num_o in [2, 4, 8]:
    #         for beta_w in [0, 0.01, 0.1]:
    #             params.append([a_squared_c_ppo_continuous, dict(game='dm-cheetah', run=r, tasks=True, remark='vis',
    #                                                             num_o=num_o, beta_weight=beta_w)])

    algo, param = params[cf.i]
    algo(**param)
    # a_squared_c_ppo_continuous(**params[cf.i])
    exit()


def set_tasks(config):
    if config.game == 'dm-walker':
        tasks = ['walk', 'run']
    elif config.game == 'dm-finger':
        tasks = ['turn_easy', 'turn_hard']
    elif config.game == 'dm-reacher':
        tasks = ['easy', 'hard']
    elif config.game == 'dm-cartpole-b':
        tasks = ['balance', 'balance_sparse']
        config.game = 'dm-cartpole'
    elif config.game == 'dm-cartpole-s':
        tasks = ['swingup', 'swingup_sparse']
        config.game = 'dm-cartpole'
    elif config.game == 'dm-fish':
        tasks = ['upright', 'downleft']
    elif config.game == 'dm-hopper':
        tasks = ['stand', 'hop']
    elif config.game == 'dm-acrobot':
        tasks = ['swingup', 'swingup_sparse']
    elif config.game == 'dm-manipulator':
        tasks = ['bring_ball', 'bring_peg']
    elif config.game == 'dm-cheetah':
        tasks = ['run', 'backward']
    else:
        raise NotImplementedError

    games = ['%s-%s' % (config.game, t) for t in tasks]
    config.tasks = [Task(g) for g in games]
    config.game = games[0]


def a_squared_c_ppo_continuous(**kwargs):
    generate_tag(kwargs)
    kwargs.setdefault('log_level', 0)
    kwargs.setdefault('num_o', 4)
    kwargs.setdefault('learning', 'all')
    kwargs.setdefault('gate', nn.ReLU())
    kwargs.setdefault('freeze_v', False)
    kwargs.setdefault('opt_ep', 5)
    kwargs.setdefault('entropy_weight', 0.01)
    kwargs.setdefault('tasks', False)
    kwargs.setdefault('max_steps', 2e6)
    kwargs.setdefault('beta_weight', 0)
    config = Config()
    config.merge(kwargs)

    if config.tasks:
        set_tasks(config)

    if 'dm-humanoid' in config.game:
        hidden_units = (128, 128)
    else:
        hidden_units = (64, 64)

    config.task_fn = lambda: Task(config.game)
    config.eval_env = config.task_fn()

    config.network_fn = lambda: OptionGaussianActorCriticNet(
        config.state_dim, config.action_dim,
        num_options=config.num_o,
        actor_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        critic_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        option_body_fn=lambda: FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
    )
    config.optimizer_fn = lambda params: torch.optim.Adam(params, 3e-4, eps=1e-5)
    config.discount = 0.99
    config.use_gae = True
    config.gae_tau = 0.95
    config.gradient_clip = 0.5
    config.rollout_length = 2048
    config.optimization_epochs = config.opt_ep
    config.mini_batch_size = 64
    config.ppo_ratio_clip = 0.2
    config.log_interval = 2048
    config.state_normalizer = MeanStdNormalizer()
    run_steps(ASquaredCPPOAgent(config))


def a_squared_c_a2c_continuous(**kwargs):
    generate_tag(kwargs)
    kwargs.setdefault('log_level', 0)
    kwargs.setdefault('num_o', 4)
    kwargs.setdefault('learning', 'all')
    kwargs.setdefault('gate', nn.ReLU())
    kwargs.setdefault('freeze_v', False)
    kwargs.setdefault('opt_ep', 5)
    kwargs.setdefault('entropy_weight', 0.01)
    kwargs.setdefault('tasks', False)
    kwargs.setdefault('max_steps', 2e6)
    config = Config()
    config.merge(kwargs)

    if config.tasks:
        set_tasks(config)

    if 'dm-humanoid' in config.game:
        hidden_units = (128, 128)
    else:
        hidden_units = (64, 64)

    config.num_workers = 16
    config.task_fn = lambda: Task(config.game, num_envs=config.num_workers)
    config.eval_env = Task(config.game)

    config.network_fn = lambda: OptionGaussianActorCriticNet(
        config.state_dim, config.action_dim,
        num_options=config.num_o,
        actor_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        critic_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        option_body_fn=lambda: FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
    )
    config.optimizer_fn = lambda params: torch.optim.Adam(params, 3e-4, eps=1e-5)
    config.discount = 0.99
    config.use_gae = True
    config.gae_tau = 0.95
    config.gradient_clip = 0.5
    config.rollout_length = 5
    config.state_normalizer = MeanStdNormalizer()
    run_steps(ASquaredCA2CAgent(config))


def ppo_continuous(**kwargs):
    generate_tag(kwargs)
    kwargs.setdefault('log_level', 0)
    kwargs.setdefault('gate', nn.ReLU())
    kwargs.setdefault('tasks', False)
    kwargs.setdefault('max_steps', 2e6)
    config = Config()
    config.merge(kwargs)

    if config.tasks:
        set_tasks(config)

    if 'dm-humanoid' in config.game:
        hidden_units = (128, 128)
    else:
        hidden_units = (64, 64)

    config.task_fn = lambda: Task(config.game)
    config.eval_env = config.task_fn()

    config.network_fn = lambda: GaussianActorCriticNet(
        config.state_dim, config.action_dim,
        actor_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        critic_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate))
    config.optimizer_fn = lambda params: torch.optim.Adam(params, 3e-4, eps=1e-5)
    config.discount = 0.99
    config.use_gae = True
    config.gae_tau = 0.95
    config.gradient_clip = 0.5
    config.rollout_length = 2048
    config.optimization_epochs = 10
    config.mini_batch_size = 64
    config.ppo_ratio_clip = 0.2
    config.log_interval = 2048
    config.state_normalizer = MeanStdNormalizer()
    run_steps(PPOAgent(config))


def ahp_ppo_continuous(**kwargs):
    generate_tag(kwargs)
    kwargs.setdefault('log_level', 0)
    kwargs.setdefault('num_o', 4)
    kwargs.setdefault('gate', nn.ReLU())
    kwargs.setdefault('opt_ep', 10)
    kwargs.setdefault('entropy_weight', 0.01)
    kwargs.setdefault('tasks', False)
    kwargs.setdefault('max_steps', 2e6)
    config = Config()
    config.merge(kwargs)

    if config.tasks:
        set_tasks(config)

    if 'dm-humanoid' in config.game:
        hidden_units = (128, 128)
    else:
        hidden_units = (64, 64)

    config.task_fn = lambda: Task(config.game)
    config.eval_env = config.task_fn()

    config.network_fn = lambda: OptionGaussianActorCriticNet(
        config.state_dim, config.action_dim,
        num_options=config.num_o,
        actor_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        critic_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        option_body_fn=lambda: FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
    )
    config.optimizer_fn = lambda params: torch.optim.Adam(params, 3e-4, eps=1e-5)
    config.discount = 0.99
    config.use_gae = True
    config.gae_tau = 0.95
    config.gradient_clip = 0.5
    config.rollout_length = 2048
    config.optimization_epochs = config.opt_ep
    config.mini_batch_size = 64
    config.ppo_ratio_clip = 0.2
    config.log_interval = 2048
    config.state_normalizer = MeanStdNormalizer()
    run_steps(AHPPPOAgent(config))


def iopg_continuous(**kwargs):
    generate_tag(kwargs)
    kwargs.setdefault('log_level', 0)
    kwargs.setdefault('num_o', 4)
    kwargs.setdefault('gate', nn.ReLU())
    kwargs.setdefault('tasks', False)
    kwargs.setdefault('max_steps', 2e6)
    config = Config()
    config.merge(kwargs)

    if config.tasks:
        set_tasks(config)

    if 'dm-humanoid' in config.game:
        hidden_units = (128, 128)
    else:
        hidden_units = (64, 64)

    config.num_workers = 16
    config.task_fn = lambda: Task(config.game, num_envs=config.num_workers)
    config.eval_env = Task(config.game)

    config.network_fn = lambda: OptionGaussianActorCriticNet(
        config.state_dim, config.action_dim,
        num_options=config.num_o,
        actor_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        critic_body=FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
        option_body_fn=lambda: FCBody(config.state_dim, hidden_units=hidden_units, gate=config.gate),
    )
    config.optimizer_fn = lambda params: torch.optim.Adam(params, 3e-4, eps=1e-5)
    config.discount = 0.99
    config.use_gae = True
    config.gae_tau = 0.95
    config.gradient_clip = 0.5
    config.state_normalizer = MeanStdNormalizer()
    run_steps(IOPGAgent(config))


if __name__ == '__main__':
    mkdir('log')
    mkdir('data')
    random_seed()
    set_one_thread()

    # select_device(0)
    # batch_atari()

    select_device(-1)
    batch_mujoco()

    # game = 'HalfCheetah-v2'
    game = 'Walker2d-v2'
    # game = 'Swimmer-v2'
    # game = 'dm-walker-walk'
    # game = 'dm-fish-upright'
    # game = 'dm-fish-swim'
    # game = 'dm-fish'
    # game = 'dm-cartpole-s'
    # game = 'dm-cheetah-run'
    # game = 'dm-cheetah-backward'
    # game = 'dm-fish-downleft'
    # ppo_continuous(
    #     game=game,
    #     # game='dm-walker',
    #     tasks=False,
    #     log_level=1,
    #     gate=nn.ReLU(),
    # )

    # a_squared_c_a2c_continuous(
    #     game=game,
    #     # learning='all',
    #     learning='alt',
    #     log_level=1,
    #     num_o=4,
    #     opt_ep=10,
    #     freeze_v=False,
    #     tasks=False,
    #     gate=nn.Tanh(),
    # )

    # a_squared_c_ppo_continuous(
    #     game=game,
    #     learning='all',
    #     log_level=1,
    #     num_o=4,
    #     opt_ep=5,
    #     freeze_v=False,
    #     tasks=False,
    #     gate=nn.ReLU(),
    #     # max_steps=4e3,
    # )

    # ahp_ppo_continuous(
    #     game=game,
    #     learning='all',
    #     log_level=1,
    #     num_o=4,
    #     opt_ep=5,
    #     freeze_v=False,
    #     tasks=False,
    #     gate=nn.ReLU(),
    #     # max_steps=4e3,
    # )

    iopg_continuous(
        game=game,
        log_level=1,
        num_o=4,
        tasks=False,
        gate=nn.Tanh(),
        # max_steps=4e3,
    )

    # game = 'AlienNoFrameskip-v4'
    # # OC_pixel(
    # #     game=game,
    # #     verify=True,
    # # )
    # IO_pixel(
    #     game=game,
    #     pi_hat_grad='posterior',
    #     verify=False,
    #     random_option=False,
    #     control_type='pi',
    #     pretrained_phi=True,
    # )
    #
    # from examples import *

    # a2c_feature(game='LunarLander-v2')
    # option_critic_feature(game='CartPole-v0')
    # IOPG_feature(
    #     # game='CartPole-v0',
    #     game='LunarLander-v2',
    #     # game='Acrobot-v1',
    #     # pi_hat_grad='sample',
    #     # pi_hat_grad='expected',
    #     pi_hat_grad='posterior',
    #     beta_grad='direct',
    #     # beta_grad='indirect',
    #     ent_hat=0.1,
    #     beta_reg=0.01,
    # )
