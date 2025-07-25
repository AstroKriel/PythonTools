## START OF MODULE


## ###############################################################
## DEPENDENCIES
## ###############################################################

from jormi.ww_io import io_manager, shell_manager


## ###############################################################
## FUNCTIONS
## ###############################################################

def submit_job(
    directory    : str,
    file_name    : str,
    check_status : bool = False,
  ) -> bool:
  if check_status and is_job_already_in_queue(directory, file_name):
    print("Job is already currently running:", file_name)
    return False
  print("Submitting job:", file_name)
  try:
    shell_manager.execute_shell_command(f"qsub {file_name}", working_directory=directory, enforce_shell=True)
    return True
  except RuntimeError as error:
    print(f"Failed to submit job `{file_name}`: {error}")
    return False

def is_job_already_in_queue(
    directory : str,
    file_name : str,
  ) -> bool:
  """Checks if a job name is already in the queue."""
  file_path = io_manager.combine_file_path_parts([directory, file_name])
  if not io_manager.does_file_exist(file_path=file_path):
    print(f"`{file_name}` job file does not exist in: {directory}")
    return False
  job_tag = get_job_tag_from_pbs_script(file_path)
  if not job_tag:
    print(f"`#PBS -N` not found in job file: {file_name}")
    return False
  queued_jobs = get_list_of_queued_jobs()
  if not queued_jobs: return False
  queued_job_tags = [
    job_tag
    for _, job_tag in queued_jobs
  ]
  return job_tag in queued_job_tags

def get_job_tag_from_pbs_script(file_path : str) -> str | None:
  """Gets the job name from a PBS job script."""
  with open(file_path, "r") as file_pointer:
    for line in file_pointer:
      if "#PBS -N" in line:
        return line.strip().split(" ")[-1] if line.strip() else None
  return None

def get_list_of_queued_jobs() -> list[tuple[str, str]] | None:
  """Collects all job (id, name) pairs currently in the queue."""
  try:
    raw_output = shell_manager.execute_shell_command(
      command="qstat -f",
      timeout_seconds=60,
    )
    jobs = []
    job_id = None
    job_tag = None
    for line in raw_output.splitlines():
      stripped = line.strip()
      if stripped.startswith("Job Id:"):
        if job_id and job_tag: jobs.append((job_id, job_tag))
        job_id = stripped.split("Job Id:")[-1].strip().split(".")[0]
        job_tag = None # reset
      elif "Job_Name =" in stripped:
        job_tag = stripped.split("Job_Name =")[-1].strip()
    if job_id and job_tag:
      jobs.append((job_id, job_tag))
    return jobs if jobs else []
  except RuntimeError as error:
    print(f"Error retrieving job info from the queue: {error}")
    return None


## END OF MODULE