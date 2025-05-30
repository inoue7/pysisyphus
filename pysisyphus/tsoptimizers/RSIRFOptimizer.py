# [1] https://doi.org/10.1007/s002140050387
#     Bofill, 1998


import numpy as np

from pysisyphus.tsoptimizers.TSHessianOptimizer import TSHessianOptimizer

import torch

class RSIRFOptimizer(TSHessianOptimizer):
    def optimize(self):
        energy, gradient, H, eigvals, eigvecs, resetted = self.housekeeping()
        self.update_ts_mode(eigvals, eigvecs)

        self.log(
            "Using projection to construct image potential gradient "
            f"and hessian for root(s) {self.roots}."
        )
        # Projection matrix to construct g* and H*
        if isinstance(H, torch.Tensor):
            P = torch.eye(self.geometry.coords.size, device=H.device, dtype=H.dtype)
            for root in self.roots:
                trans_vec = eigvecs[:, root]
                P -= 2 * torch.outer(trans_vec, trans_vec)
            H_star = P @ H
            eigvals_, eigvecs_ = torch.linalg.eigh(H_star)
        else:
            P = np.eye(self.geometry.coords.size)
            for root in self.roots:
                trans_vec = eigvecs[:, root]
                P -= 2 * np.outer(trans_vec, trans_vec)
            H_star = P.dot(H)
            eigvals_, eigvecs_ = np.linalg.eigh(H_star)
            # Neglect small eigenvalues
            eigvals_, eigvecs_ = self.filter_small_eigvals(eigvals_, eigvecs_)

        if isinstance(H, torch.Tensor):
            grad_star = P @ gradient
        else:
            grad_star = P.dot(gradient)
        step = self.get_rs_step(eigvals_, eigvecs_, grad_star, name="RS-I-RFO")

        self.predicted_energy_changes.append(self.rfo_model(gradient, self.H, step))
        if isinstance(step, torch.Tensor):
            step = step.cpu().numpy()
        return step
