import os
import argparse
import torch
import numpy as np

from core.ppo_trainer import PPOTrainer, ppo_config
from competitive_pong import make_envs
from core.utils import verify_log_dir, pretty_print, Timer, evaluate, \
    adversarial_evaluate, summary, save_progress, FrameStackTensor, step_envs

def attack(is_attack=True, is_render=False):
    config = ppo_config
    seed = 100 # args.seed
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    torch.set_num_threads(1)
    # env_id = "Pong-v0"
    env_id = "CompetitivePong-v0"
    load_dir = "./data/mirror/PPO"
    load_suffix = "best4"
    log_dir = "./data/attack"
    iteration = 0
    num_envs = 1
    test = False
    tournament = False

    eval_envs = make_envs(
        env_id=env_id,
        seed=seed,
        log_dir=log_dir,
        num_envs=num_envs,
        asynchronous=False,
        resized_dim=config.resized_dim
    )

    frame_stack = 4 if not test else 1

    trainer = PPOTrainer(eval_envs, config, frame_stack, _test=test)
    #file_path = os.path.join(load_dir, "checkpoint-%s.pkl"%load_suffix)
    trainer.load_w(load_dir, load_suffix)

    frame_stack_tensor = FrameStackTensor(
        num_envs, eval_envs.observation_space.shape, frame_stack, config.device)

    eval_timer = Timer()
    evaluate_rewards, evaluate_lengths = adversarial_evaluate(
        trainer, eval_envs, frame_stack, 20, is_render=is_render, is_attack=is_attack)
    evaluate_stat = summary(evaluate_rewards, "episode_reward")
    if evaluate_lengths:
        evaluate_stat.update(
            summary(evaluate_lengths, "episode_length"))
    evaluate_stat.update(dict(
        win_rate=float(
            sum(np.array(evaluate_rewards) >= 0) / len(
                evaluate_rewards)),
        evaluate_time=eval_timer.now,
        evaluate_iteration=iteration
    ))

    print(evaluate_stat)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--render",
        default=False,
        type=bool,
    )
    parser.add_argument(
        "--no-attack",
        default=False,
        type=bool,
    )
    args = parser.parse_args()
    attack(is_attack=(not args.no_attack), is_render=args.render)
